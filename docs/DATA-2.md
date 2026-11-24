# DATA-2: Data Quality and Testing Framework

## Overview

A custom, configuration-driven data quality framework for
the wealth management data engineering platform.

The framework separates YAML declarations, configuration
validation, execution logic, and database-specific adapters.

## Architecture

YAML Configurations
    -> Configuration Parser
    -> Quality Engine
    -> Database Adapter
    -> Count-Based Validation
    -> Severity Enforcement

## Supported Checks

| Check | Purpose |
|---|---|
| null_check | Detect missing required values |
| unique_key | Detect duplicate composite keys |
| range_check | Detect numeric values outside configured bounds |
| cross_tenant_check | Detect invalid tenant-scoped relationships |
| row_count_reconciliation | Detect unexpected row count differences |

## Severity Policy

- PASS: No violations. Continue execution.
- WARNING: Log violations and continue execution.
- ERROR: Fail the quality gate and block downstream tasks.

The command-line runner returns exit code 1 for ERROR-level
violations and exit code 0 otherwise.

## Configuration Coverage

The framework currently supports 10 Silver tables:

- silver_accounts
- silver_advisors
- silver_clients
- silver_fees
- silver_holdings
- silver_portfolios
- silver_securities
- silver_statements
- silver_trades
- silver_transactions

A total of 52 quality checks are configured.

## Tenant Integrity

Composite keys include organisation_id, entity ID,
and processing_date.

Cross-tenant checks validate referenced entities within
the same organisation and processing date.

These checks enforce tenant-scoped referential integrity.
They do not replace authorization controls or independent
ownership validation where entity IDs are reused across tenants.

## Running the Framework

From the project root, activate the Python environment
and load the required ClickHouse environment variables.

    set -a
    source .env
    set +a

Validate configurations:

    PYTHONPATH=. python scripts/validate_quality_configs.py

Run offline unit tests:

    python -m unittest discover -s tests/data_quality -v

Run live quality checks:

    CLICKHOUSE_HOST=localhost CLICKHOUSE_PORT=8123 \
    python -m data_quality.runner

## Integration Testing

Live integration tests use isolated synthetic tables in
the data_quality_test database.

The tests deliberately introduce corruption, verify the
expected result, remove synthetic corruption, and verify
successful recovery.

    PYTHONPATH=. python tests/integration/test_corruption_scenarios.py

The isolated baseline tables must be initialized before
running the integration tests.

## Verified Results

Local validation on November 23, 2026:

- 30 offline unit tests passed.
- 6 live integration tests passed.
- 10 Silver tables configured.
- 52 live quality checks passed.
- Zero production warnings or errors.

## Continuous Integration

GitHub Actions is configured to validate YAML declarations
and execute offline unit tests on pushes and pull requests.

Live integration tests require a running ClickHouse instance.

## Airflow Integration

The Silver quality gate is positioned before Gold
transformations so ERROR-level violations can prevent
downstream execution.

## Known Limitations

The current row-count reconciliation uses a configured
expected count. Dynamic datasets should use batch-specific
expectations or upstream reconciliation.

Range checks validate configured bounds; missing numeric
values require a separate null check.

Tenant referential integrity does not independently prove
ownership when identifiers are shared across organisations.

## Reproducible Test Suite

With Docker running and the local Python environment configured:

    ./scripts/test_data_quality.sh

This command validates configurations, runs offline unit tests,
initializes isolated synthetic test tables, executes corruption
tests, and validates the actual Silver tables.

The synthetic setup resets only the dedicated test tables.
Do not run it concurrently with integration tests.
