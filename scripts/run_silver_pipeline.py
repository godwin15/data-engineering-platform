
import os
import re
import sys
from datetime import datetime

import clickhouse_connect

DATASETS = {
    "advisors": {
        "key": "advisor_id",
        "columns": {
            "advisor_id": "String",
            "advisor_name": "Nullable(String)",
            "specialization": "Nullable(String)",
            "status": "Nullable(String)",
        },
    },
    "fees": {
        "key": "fee_id",
        "columns": {
            "fee_id": "String",
            "account_id": "String",
            "fee_type": "Nullable(String)",
            "fee_amount": "Nullable(Float64)",
            "currency": "Nullable(String)",
        },
    },
    "statements": {
        "key": "statement_id",
        "columns": {
            "statement_id": "String",
            "account_id": "String",
            "opening_balance": "Nullable(Float64)",
            "total_deposits": "Nullable(Float64)",
            "total_withdrawals": "Nullable(Float64)",
            "total_fees": "Nullable(Float64)",
            "ending_balance": "Nullable(Float64)",
            "currency": "Nullable(String)",
        },
    },
    "trades": {
        "key": "trade_id",
        "columns": {
            "trade_id": "String",
            "account_id": "String",
            "security_id": "String",
            "trade_type": "Nullable(String)",
            "quantity": "Nullable(Int64)",
            "price": "Nullable(Float64)",
            "trade_value": "Nullable(Float64)",
        },
    },
}

def main():
    client = clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=os.getenv("CLICKHOUSE_USER", "default"),
        password=os.environ["CLICKHOUSE_PASSWORD"],
        database="wealth_management",
    )

    for dataset, cfg in DATASETS.items():
        print(f"\nProcessing {dataset}...")

        key = cfg["key"]
        columns = cfg["columns"]
        required = ["organisation_id", key]

        if "account_id" in columns:
            required.append("account_id")
        if "security_id" in columns:
            required.append("security_id")

        stage = f"silver_{dataset}_staging"
        target = f"silver_{dataset}"

        column_defs = [
            "organisation_id String",
            *[f"{name} {dtype}" for name, dtype in columns.items()],
            "processing_date Date",
            "ingested_at DateTime DEFAULT now()",
        ]

        client.command(f"DROP TABLE IF EXISTS {stage}")

        client.command(f"""
            CREATE TABLE {stage}
            (
                {", ".join(column_defs)}
            )
            ENGINE = MergeTree()
            PARTITION BY toYYYYMM(processing_date)
            ORDER BY (organisation_id, {key}, processing_date)
        """)

        
        select_cols = [
            f"assumeNotNull(b.{name}) AS {name}"
            if name in required
            else f"b.{name} AS {name}"
            for name in columns
        ]

        conditions = [
            f"b.{name} IS NOT NULL"
            for name in required
        ]

        conditions += [
            "b.processing_date IS NOT NULL",
            "match(assumeNotNull(b.processing_date), '^[0-9]{4}-[0-9]{2}-[0-9]{2}$')",
            "isNotNull(parseDateTimeBestEffortOrNull(assumeNotNull(b.processing_date)))",
        ]

        all_columns = [
            "organisation_id",
            *columns.keys(),
            "processing_date",
        ]

        client.command(f"""
            INSERT INTO {stage} ({", ".join(all_columns)})
            SELECT
                {", ".join(all_columns)}
            FROM
            (
                SELECT
                    assumeNotNull(b.organisation_id) AS organisation_id,
                    {", ".join(select_cols)},
                    toDate(assumeNotNull(b.processing_date)) AS processing_date,
                    row_number() OVER (
                        PARTITION BY
                            b.organisation_id,
                            b.{key},
                            b.processing_date
                        ORDER BY b.{key}
                    ) AS rn
                FROM bronze_{dataset} AS b
                WHERE {" AND ".join(conditions)}
            )
            WHERE rn = 1
        """)


        result = client.query(f"""
            SELECT
                count(),
                uniqExact(tuple(organisation_id, {key}, processing_date))
            FROM {stage}
        """).result_rows[0]

        count, unique_count = result

        if count == 0 or count != unique_count:
            raise RuntimeError(
                f"Validation failed for {dataset}: "
                f"rows={count}, unique={unique_count}"
            )

        backup = f"{target}_backup"

        client.command(f"DROP TABLE IF EXISTS {backup}")

        existing = client.query(f"""
            EXISTS TABLE {target}
        """).result_rows[0][0]

        if existing:
            client.command(f"""
                RENAME TABLE
                    {target} TO {backup},
                    {stage} TO {target}
            """)
        else:
            client.command(f"RENAME TABLE {stage} TO {target}")

        print(f"PASS: {dataset}: {count} records, {unique_count} unique keys")

    print("\nSilver pipeline completed successfully.")

if __name__ == "__main__":
    main()
