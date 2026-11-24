# Platform Health Incident Runbook

## Initial Investigation

Run the health console:

    python -m platform_health.console

Identify the affected table, anomaly rule and severity.

Inspect its upstream and downstream dependencies:

    python -m platform_health.console --impact TABLE_NAME

Review Airflow logs and recent pipeline execution history.

## Stale Data

Rule: stale_data

1. Check the latest ingestion timestamp.
2. Review the applicable ingestion or transformation job.
3. Investigate failed or skipped pipeline executions.
4. Confirm the freshness threshold is appropriate.
5. Rerun the affected pipeline after identifying the cause.
6. Execute the health console to verify recovery.

## Missing Table

Rule: missing_table

1. Confirm database connectivity and permissions.
2. Check whether the table was renamed or removed.
3. Review schema creation and transformation scripts.
4. Restore or rebuild the table using approved procedures.
5. Verify downstream dependencies and data quality.

## Empty Table

Rule: empty_table

1. Inspect upstream row counts.
2. Review filters and transformation conditions.
3. Check source availability and ingestion failures.
4. Rebuild only after identifying the root cause.
5. Verify record counts and quality checks.

## Volume Anomaly

Rule: volume_change

1. Compare the current and previous row counts.
2. Investigate unexpected source changes.
3. Check duplicate records and missing partitions.
4. Run the DATA-2 quality framework.
5. Determine whether the change is legitimate.

## Storage Growth

Rule: storage_growth

1. Review ClickHouse storage metadata.
2. Inspect recent data loads and partition growth.
3. Investigate duplication and retention policies.
4. Check available disk capacity.
5. Avoid deleting data without an approved procedure.

## Unavailable Metrics

Rules: unknown_freshness, unknown_storage, unknown_volume

1. Determine whether the table engine supports the metric.
2. Check ingestion timestamp availability.
3. Inspect permissions and metadata queries.
4. Add appropriate telemetry where possible.
5. Do not interpret unavailable metrics as zero.

## Circular Dependencies

Rule: lineage_cycle

1. Export and inspect the lineage graph.
2. Locate the transformation definitions in the cycle.
3. Correct the dependency design.
4. Regenerate lineage configurations.
5. Run all lineage tests before deployment.

## Parser and Collection Errors

Rules: parser_error, collection_error

1. Check configuration syntax and database connectivity.
2. Inspect the reported error.
3. Correct the source definition or connection issue.
4. Rerun monitoring.
5. Do not close incidents based on incomplete observations.

## Recovery Verification

Run:

    python -m data_quality.runner
    python -m platform_health.console
    python -m platform_health.console --strict

Confirm that the original anomaly is absent and that
the corresponding alert has been resolved.

Record the root cause, remediation and verification
results before closing the incident.
