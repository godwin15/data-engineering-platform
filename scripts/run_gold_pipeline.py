import os
import clickhouse_connect

DATABASE = "wealth_management"

from pipeline_config import load_models

from gold_tenant_guard import validate_gold_sql

GOLD_MODELS = load_models("gold.yaml")

for model_name, model_config in GOLD_MODELS.items():
    try:
        validate_gold_sql(model_config["sql"])
    except ValueError as exc:
        raise ValueError(
            f"Unsafe Gold model {model_name}: {exc}"
        ) from exc


def main():
    client = clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=os.getenv("CLICKHOUSE_USER", "default"),
        password=os.environ["CLICKHOUSE_PASSWORD"],
        database=DATABASE,
    )

    for name, config in GOLD_MODELS.items():
        target = f"gold_{name}"
        stage = f"{target}_staging"
        backup = f"{target}_backup"

        print(f"\nBuilding {target}...")

        # Remove an incomplete staging table from a previous run.
        client.command(f"DROP TABLE IF EXISTS {stage}")

        # Create staging table with schema inferred from SQL.
        client.command(f"""
            CREATE TABLE {stage}
            ENGINE = MergeTree()
            ORDER BY tuple()
            AS
            SELECT *
            FROM ({config['sql']})
            LIMIT 0
        """)

        # Load transformed data into staging.
        client.command(f"""
            INSERT INTO {stage}
            SELECT *
            FROM ({config['sql']})
        """)

        # Validate record counts and unique business keys.
        key_columns = [
            "organisation_id",
            *[x.strip() for x in config["key"].split(",")],
            "processing_date",
        ]

        key_expr = ", ".join(key_columns)

        count, unique_count, null_keys = client.query(f"""
            SELECT
                count(),
                uniqExact(tuple({key_expr})),
                countIf(
                    {" OR ".join(
                        f"isNull({column})"
                        for column in key_columns
                    )}
                )
            FROM {stage}
        """).result_rows[0]

        if count == 0 or count != unique_count or null_keys != 0:
            raise RuntimeError(
                f"{target} failed validation: "
                f"{count} rows, "
                f"{unique_count} unique keys, "
                f"{null_keys} null keys"
            )

        # Additional financial validation for statement summaries.
        if name == "statement_summary":
            missing, mismatches = client.query(f"""
                SELECT
                    sum(missing_financial_values),
                    sum(reconciliation_errors)
                FROM {stage}
            """).result_rows[0]

            if missing != 0 or mismatches != 0:
                raise RuntimeError(
                    f"{target} failed financial validation: "
                    f"{missing} missing-value records, "
                    f"{mismatches} reconciliation errors"
                )

        # Preserve a backup of the previous Gold table.
        # This local prototype replacement is not fully atomic.
        existing = client.query(
            f"EXISTS TABLE {target}"
        ).result_rows[0][0]

        if existing:
            client.command(f"DROP TABLE IF EXISTS {backup}")
            client.command(
                f"RENAME TABLE {target} TO {backup}, "
                f"{stage} TO {target}"
            )
        else:
            client.command(f"RENAME TABLE {stage} TO {target}")

        print(
            f"PASS: {target}: "
            f"{count} rows, {unique_count} unique keys"
        )

    print("\nGold pipeline completed successfully.")


if __name__ == "__main__":
    main()
