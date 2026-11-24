import os

from data_quality.schema import QualityCheck
from data_quality.engine import QualityEngine
from data_quality.adapters.clickhouse import ClickHouseCountAdapter


DATABASE = "data_quality_test"


def make_check(table, name, check_type, parameters, severity="ERROR"):
    return QualityCheck(
        database=DATABASE,
        table=table,
        name=name,
        check_type=check_type,
        severity=severity,
        parameters=parameters,
    )


checks = [
    make_check(
        "test_clients",
        "client_name_required",
        "null_check",
        {"column": "client_name"},
    ),
    make_check(
        "test_clients",
        "client_key_unique",
        "unique_key",
        {
            "columns": [
                "organisation_id",
                "client_id",
                "processing_date",
            ]
        },
    ),
    make_check(
        "test_accounts",
        "account_balance_range",
        "range_check",
        {
            "column": "balance",
            "min": 0,
            "max": 10000,
        },
    ),
    make_check(
        "test_accounts",
        "account_client_tenant_integrity",
        "cross_tenant_check",
        {
            "entity_column": "client_id",
            "tenant_column": "organisation_id",
            "reference_table": "test_clients",
        },
    ),
    make_check(
        "test_clients",
        "client_row_count",
        "row_count_reconciliation",
        {"expected_count": 4},
        severity="WARNING",
    ),
]


def main():
    adapter = ClickHouseCountAdapter(
        password=os.environ["CLICKHOUSE_PASSWORD"]
    )

    try:
        engine = QualityEngine(adapter)
        results = engine.execute(checks)

        print("\n=== LIVE DATA QUALITY REPORT ===\n")

        for result in results:
            print(
                f"{result.table}.{result.name}: "
                f"{result.status} "
                f"(violations={result.violation_count})"
            )

        failed = engine.should_fail_pipeline(results)

        print(f"\nExecuted checks: {len(results)}")
        print(f"Pipeline failure: {failed}")

        return 1 if failed else 0

    finally:
        adapter.close()


if __name__ == "__main__":
    raise SystemExit(main())
