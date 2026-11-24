import math
import clickhouse_connect

from data_quality.schema import QualityCheck, validate_identifier


class ClickHouseCountAdapter:
    def __init__(self, host="localhost", port=8123,
                 username="default", password=""):
        self.client = clickhouse_connect.get_client(
            host=host,
            port=port,
            username=username,
            password=password,
        )

    def count_violations(self, check: QualityCheck) -> int:
        database = validate_identifier(check.database, "database")
        table = validate_identifier(check.table, "table")
        target = f"{database}.{table}"
        params = check.parameters

        if check.check_type == "null_check":
            column = validate_identifier(params["column"], "column")
            query = (
                f"SELECT count() FROM {target} "
                f"WHERE {column} IS NULL "
                f"OR toString({column}) = ''"
            )

        elif check.check_type == "unique_key":
            columns = params["columns"]
            for column in columns:
                validate_identifier(column, "column")

            keys = ", ".join(columns)
            query = (
                "SELECT count() FROM ("
                f"SELECT {keys} FROM {target} "
                f"GROUP BY {keys} HAVING count() > 1"
                ")"
            )

        elif check.check_type == "row_count_reconciliation":
            expected = params["expected_count"]

            if type(expected) is not int or expected < 0:
                raise ValueError(
                    "expected_count must be a nonnegative integer")

            query = f"SELECT abs(toInt64(count()) - {expected}) FROM {target}"

        elif check.check_type == "range_check":
            column = validate_identifier(params["column"], "column")
            minimum = params.get("min")
            maximum = params.get("max")

            if minimum is None and maximum is None:
                raise ValueError("range_check requires min or max")

            for value in (minimum, maximum):
                if value is not None and (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                ):
                    raise ValueError("range bounds must be numeric")

                if isinstance(value, float) and not math.isfinite(value):
                    raise ValueError("range bounds must be finite")

            if minimum is not None and maximum is not None:
                if minimum > maximum:
                    raise ValueError("min cannot exceed max")

            conditions = []

            if minimum is not None:
                conditions.append(f"{column} < {minimum}")

            if maximum is not None:
                conditions.append(f"{column} > {maximum}")

            query = (
                f"SELECT count() FROM {target} "
                f"WHERE {' OR '.join(conditions)}"
            )
        elif check.check_type == "cross_tenant_check":
            entity_column = validate_identifier(
                params["entity_column"], "entity_column"
            )
            tenant_column = validate_identifier(
                params["tenant_column"], "tenant_column"
            )
            reference_table = validate_identifier(
                params["reference_table"], "reference_table"
            )
            reference_entity_column = validate_identifier(
                params.get("reference_entity_column", entity_column),
                "reference_entity_column",
            )
            reference_tenant_column = validate_identifier(
                params.get("reference_tenant_column", tenant_column),
                "reference_tenant_column",
            )

            source_date = validate_identifier(
                params.get("processing_date_column", "processing_date"),
                "processing_date_column",
            )
            reference_date = validate_identifier(
                params.get("reference_date_column", "processing_date"),
                "reference_date_column",
            )

            query = (
                f"SELECT count() FROM {target} AS a "
                f"WHERE NOT EXISTS ("
                f"SELECT 1 FROM {database}.{reference_table} AS c "
                f"WHERE c.{reference_tenant_column} = a.{tenant_column} "
                f"AND c.{reference_entity_column} = a.{entity_column} "
                f"AND c.{reference_date} = a.{source_date}"
                f")"
            )

        else:
            raise NotImplementedError(
                f"ClickHouse adapter does not yet support: {check.check_type}"
            )

        result = self.client.query(query).result_rows
        return int(result[0][0])

    def close(self):
        self.client.close()
