import os
import sys
import clickhouse_connect

DATABASE = "wealth_management"

TABLES = {
    "silver_clients": ("client_id", 210),
    "silver_accounts": ("account_id", 420),
    "silver_portfolios": ("portfolio_id", 420),
    "silver_securities": ("security_id", 105),
    "silver_holdings": ("holding_id", 1260),
    "silver_transactions": ("transaction_id", 420),
    "silver_advisors": ("advisor_id", 63),
    "silver_fees": ("fee_id", 420),
    "silver_statements": ("statement_id", 420),
    "silver_trades": ("trade_id", 420),
    "gold_account_activity": ("account_id", 420),
    "gold_portfolio_holdings": ("portfolio_id, security_id", 1260),
    "gold_statement_summary": ("account_id", 420),
}


def main():
    client = clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=os.getenv("CLICKHOUSE_USER", "default"),
        password=os.environ["CLICKHOUSE_PASSWORD"],
        database=DATABASE,
    )

    failures = []

    for table, (key, expected) in TABLES.items():
        try:
            count, unique_count = client.query(f"""
                SELECT
                    count(),
                    uniqExact(tuple(
                        organisation_id, {key}, processing_date
                    ))
                FROM {table}
            """).result_rows[0]

            if count != expected or unique_count != count:
                failures.append(
                    f"{table}: rows={count}, "
                    f"unique={unique_count}, expected={expected}"
                )
                print(f"FAIL: {table}")
            else:
                print(f"PASS: {table}: {count} rows")

        except Exception as exc:
            failures.append(f"{table}: {exc}")
            print(f"ERROR: {table}: {exc}")

    # Reconciliation flags are produced by the Gold model.
    try:
        missing, mismatches = client.query("""
            SELECT
                sum(missing_financial_values),
                sum(reconciliation_errors)
            FROM gold_statement_summary
        """).result_rows[0]

        if missing != 0 or mismatches != 0:
            failures.append(
                f"Financial reconciliation: "
                f"missing={missing}, mismatches={mismatches}"
            )
        else:
            print("PASS: Financial reconciliation")

    except Exception as exc:
        failures.append(f"Financial reconciliation: {exc}")

    if failures:
        print("\nDATA QUALITY FAILED:")
        for failure in failures:
            print(f"- {failure}")
        sys.exit(1)

    print("\nDATA QUALITY PASSED: All 13 tables validated.")


if __name__ == "__main__":
    main()
