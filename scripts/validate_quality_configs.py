import math
from collections import Counter

from data_quality.schema import discover_configs, validate_identifier


def main():
    checks = discover_configs("data_quality/config")
    tables = {check.table for check in checks}

    required_types = {
        "null_check",
        "unique_key",
        "range_check",
        "cross_tenant_check",
        "row_count_reconciliation",
    }

    required_tables = {
        f"silver_{name}" for name in (
            "accounts", "advisors", "clients", "fees",
            "holdings", "portfolios", "securities",
            "statements", "trades", "transactions",
        )
    }

    if not required_tables.issubset(tables):
        raise ValueError(
            f"Missing tables: {required_tables - tables}"
        )

    actual_types = {check.check_type for check in checks}

    if not required_types.issubset(actual_types):
        raise ValueError(
            f"Missing check types: {required_types - actual_types}"
        )

    seen = set()

    for check in checks:
        identity = (check.database, check.table, check.name)

        if identity in seen:
            raise ValueError(f"Duplicate check: {identity}")

        seen.add(identity)
        params = check.parameters
        kind = check.check_type

        if kind in {"null_check", "range_check"}:
            validate_identifier(params["column"], "column")

        if kind == "unique_key":
            columns = params["columns"]

            if not isinstance(columns, list) or not columns:
                raise ValueError(f"Invalid unique key: {identity}")

            for column in columns:
                validate_identifier(column, "column")

            if "organisation_id" not in columns:
                raise ValueError(f"Missing tenant key: {identity}")

        if kind == "cross_tenant_check":
            for field in (
                "entity_column",
                "tenant_column",
                "reference_table",
            ):
                validate_identifier(params[field], field)

        if kind == "row_count_reconciliation":
            count = params["expected_count"]

            if type(count) is not int or count < 0:
                raise ValueError(f"Invalid expected count: {identity}")

        if kind == "range_check":
            minimum = params.get("min")
            maximum = params.get("max")

            if minimum is None and maximum is None:
                raise ValueError(f"Missing range bounds: {identity}")

            for value in (minimum, maximum):
                if value is not None and type(value) not in (int, float):
                    raise ValueError(f"Invalid range bound: {identity}")

                if isinstance(value, float) and not math.isfinite(value):
                    raise ValueError(f"Nonfinite range bound: {identity}")

            if minimum is not None and maximum is not None:
                if minimum > maximum:
                    raise ValueError(f"Reversed range: {identity}")

    print("=== CONFIGURATION VALIDATION PASSED ===")
    print(f"Tables: {len(tables)}")
    print(f"Checks: {len(checks)}")

    for kind, count in sorted(
        Counter(c.check_type for c in checks).items()
    ):
        print(f"{kind}: {count}")


if __name__ == "__main__":
    main()
