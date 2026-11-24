from data_quality.schema import QualityCheck, validate_identifier


def generate_tenant_guards(
    database,
    table,
    tenant_column,
    primary_key,
    expected_count=None,
    entity_column=None,
    reference_table=None,
):
    """Generate standard multi-tenancy quality checks."""

    validate_identifier(database, "database")
    validate_identifier(table, "table")
    validate_identifier(tenant_column, "tenant_column")

    if not isinstance(primary_key, list) or not primary_key:
        raise ValueError("primary_key must be a nonempty list")

    for column in primary_key:
        validate_identifier(column, "primary_key column")

    if tenant_column not in primary_key:
        raise ValueError(
            "Multi-tenant primary keys must include the tenant column"
        )

    def make_check(name, check_type, severity="ERROR", **parameters):
        return QualityCheck(
            database=database,
            table=table,
            name=name,
            check_type=check_type,
            severity=severity,
            parameters=parameters,
        )

    checks = [
        make_check(
            "auto_tenant_not_null",
            "null_check",
            column=tenant_column,
        ),
        make_check(
            "auto_primary_key_unique",
            "unique_key",
            columns=primary_key,
        ),
    ]

    if expected_count is not None:
        if type(expected_count) is not int or expected_count < 0:
            raise ValueError("expected_count must be a nonnegative integer")

        checks.append(
            make_check(
                "auto_row_count",
                "row_count_reconciliation",
                severity="WARNING",
                expected_count=expected_count,
            )
        )

    if (entity_column is None) != (reference_table is None):
        raise ValueError(
            "entity_column and reference_table must be supplied together"
        )

    if entity_column is not None:
        validate_identifier(entity_column, "entity_column")
        validate_identifier(reference_table, "reference_table")

        checks.append(
            make_check(
                "auto_cross_tenant",
                "cross_tenant_check",
                entity_column=entity_column,
                tenant_column=tenant_column,
                reference_table=reference_table,
            )
        )

    return checks
