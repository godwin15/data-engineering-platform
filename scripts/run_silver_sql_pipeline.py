import os
import re
from pathlib import Path

import clickhouse_connect


DATABASE = "wealth_management"
SQL_DIR = Path("/opt/airflow/sql/silver")

DATASETS = {
    "clients": "client_id",
    "accounts": "account_id",
    "portfolios": "portfolio_id",
    "securities": "security_id",
    "holdings": "holding_id",
    "transactions": "transaction_id",
}


def main():
    client = clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=os.getenv("CLICKHOUSE_USER", "default"),
        password=os.environ["CLICKHOUSE_PASSWORD"],
        database=DATABASE,
    )

    for dataset, key in DATASETS.items():
        target = f"{DATABASE}.silver_{dataset}"
        stage = f"{DATABASE}.silver_{dataset}_staging"
        backup = f"{DATABASE}.silver_{dataset}_backup"

        sql_path = SQL_DIR / f"load_silver_{dataset}.sql"
        sql = sql_path.read_text()

        print(f"\nProcessing {dataset}...", flush=True)

        # Require the existing table to preserve its schema.
        exists = client.query(
            f"EXISTS TABLE {target}"
        ).result_rows[0][0]

        if not exists:
            raise RuntimeError(f"Missing target table: {target}")

        # Extract the INSERT statement and its SELECT logic.
        match = re.search(
            rf"INSERT\s+INTO\s+{re.escape(target)}\s*"
            r"(\([^;]*?\)\s*)?"
            r"SELECT\b[\s\S]*?;",
            sql,
            flags=re.IGNORECASE,
        )

        if not match:
            raise RuntimeError(
                f"Could not find expected INSERT statement in {sql_path}"
            )

        insert_sql = match.group(0).strip().rstrip(";")

        # Redirect INSERT to staging.
        staged_insert = re.sub(
            rf"INSERT\s+INTO\s+{re.escape(target)}",
            f"INSERT INTO {stage}",
            insert_sql,
            count=1,
            flags=re.IGNORECASE,
        )

        # Build staging with the exact target schema.
        client.command(f"DROP TABLE IF EXISTS {stage}")
        client.command(
            f"CREATE TABLE {stage} AS {target}"
        )

        # Execute existing transformation against staging.
        client.command(staged_insert)

        # Validate row counts and business-key uniqueness.
        count, unique_count, null_keys = client.query(f"""
            SELECT
                count(),
                uniqExact(
                    tuple(organisation_id, {key}, processing_date)
                ),
                countIf(
                    isNull(organisation_id)
                    OR isNull({key})
                    OR isNull(processing_date)
                )
            FROM {stage}
        """).result_rows[0]

        if count == 0 or count != unique_count or null_keys != 0:
            raise RuntimeError(
                f"Validation failed for {dataset}: "
                f"rows={count}, unique={unique_count}, "
                f"null_keys={null_keys}"
            )

        # Promote only after validation succeeds.
        client.command(f"DROP TABLE IF EXISTS {backup}")
        client.command(
            f"RENAME TABLE "
            f"{target} TO {backup}, "
            f"{stage} TO {target}"
        )

        print(
            f"PASS: {dataset}: "
            f"{count} records, {unique_count} unique keys",
            flush=True,
        )

    print("\nSilver SQL pipeline completed successfully.")


if __name__ == "__main__":
    main()
