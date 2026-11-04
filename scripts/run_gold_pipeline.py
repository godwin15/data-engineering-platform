import os
import clickhouse_connect

DATABASE = "wealth_management"

GOLD_MODELS = {
    "account_activity": {
        "key": "account_id",
        "sql": """
            SELECT
                a.organisation_id AS organisation_id,
                a.account_id AS account_id,
                a.client_id AS client_id,
                a.currency AS account_currency,
                a.processing_date AS processing_date,
                coalesce(tx.transaction_count, 0) AS transaction_count,
                coalesce(tx.transaction_amount, 0) AS transaction_amount,
                coalesce(tr.trade_count, 0) AS trade_count,
                coalesce(tr.total_trade_value, 0) AS total_trade_value,
                coalesce(f.fee_count, 0) AS fee_count,
                coalesce(f.total_fees, 0) AS total_fees
            FROM silver_accounts AS a
            LEFT JOIN (
                SELECT
                    organisation_id,
                    account_id,
                    processing_date,
                    count() AS transaction_count,
                    sum(coalesce(amount, 0)) AS transaction_amount
                FROM silver_transactions
                GROUP BY organisation_id, account_id, processing_date
            ) AS tx
                ON a.organisation_id = tx.organisation_id
                AND a.account_id = tx.account_id
                AND a.processing_date = tx.processing_date
            LEFT JOIN (
                SELECT
                    organisation_id,
                    account_id,
                    processing_date,
                    count() AS trade_count,
                    sum(coalesce(trade_value, 0)) AS total_trade_value
                FROM silver_trades
                GROUP BY organisation_id, account_id, processing_date
            ) AS tr
                ON a.organisation_id = tr.organisation_id
                AND a.account_id = tr.account_id
                AND a.processing_date = tr.processing_date
            LEFT JOIN (
                SELECT
                    organisation_id,
                    account_id,
                    processing_date,
                    count() AS fee_count,
                    sum(coalesce(fee_amount, 0)) AS total_fees
                FROM silver_fees
                GROUP BY organisation_id, account_id, processing_date
            ) AS f
                ON a.organisation_id = f.organisation_id
                AND a.account_id = f.account_id
                AND a.processing_date = f.processing_date
        """
    },

    "portfolio_holdings": {
        "key": "portfolio_id, security_id",
        "sql": """
            SELECT
                h.organisation_id AS organisation_id,
                h.portfolio_id AS portfolio_id,
                p.account_id AS account_id,
                p.portfolio_name AS portfolio_name,
                p.base_currency AS base_currency,
                h.security_id AS security_id,
                s.security_name AS security_name,
                s.ticker AS ticker,
                s.asset_type AS asset_type,
                s.currency AS security_currency,
                h.processing_date AS processing_date,
                count() AS holding_count,
                sum(coalesce(h.quantity, 0)) AS total_quantity,
                sum(coalesce(h.market_value, 0)) AS total_market_value
            FROM silver_holdings AS h
            INNER JOIN silver_portfolios AS p
                ON h.organisation_id = p.organisation_id
                AND h.portfolio_id = p.portfolio_id
                AND h.processing_date = p.processing_date
            LEFT JOIN silver_securities AS s
                ON h.organisation_id = s.organisation_id
                AND h.security_id = s.security_id
                AND h.processing_date = s.processing_date
            GROUP BY
                h.organisation_id,
                h.portfolio_id,
                p.account_id,
                p.portfolio_name,
                p.base_currency,
                h.security_id,
                s.security_name,
                s.ticker,
                s.asset_type,
                s.currency,
                h.processing_date
        """
    },

    "statement_summary": {
        "key": "account_id",
        "sql": """
            SELECT
                organisation_id,
                account_id,
                processing_date,
                count() AS statement_count,

                sum(coalesce(opening_balance, 0))
                    AS total_opening_balance,

                sum(coalesce(total_deposits, 0))
                    AS summed_deposits,

                sum(coalesce(total_withdrawals, 0))
                    AS summed_withdrawals,

                sum(coalesce(total_fees, 0))
                    AS summed_statement_fees,

                sum(coalesce(ending_balance, 0))
                    AS total_ending_balance,

                countIf(ending_balance < 0)
                    AS overdraft_count,

                countIf(
                    opening_balance IS NULL
                    OR total_deposits IS NULL
                    OR total_withdrawals IS NULL
                    OR total_fees IS NULL
                    OR ending_balance IS NULL
                ) AS missing_financial_values,

                countIf(
                    opening_balance IS NOT NULL
                    AND total_deposits IS NOT NULL
                    AND total_withdrawals IS NOT NULL
                    AND total_fees IS NOT NULL
                    AND ending_balance IS NOT NULL
                    AND abs(
                        ending_balance -
                        (
                            opening_balance
                            + total_deposits
                            - total_withdrawals
                            - total_fees
                        )
                    ) > 0.01
                ) AS reconciliation_errors

            FROM silver_statements
            GROUP BY
                organisation_id,
                account_id,
                processing_date
        """
    }
}


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
