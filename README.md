# DATA-1: Medallion Pipeline Engine

An end-to-end data engineering platform for processing synthetic wealth-management data using Python, ClickHouse, MinIO, Apache Airflow, PostgreSQL, and Docker.

## Architecture

Source CSV → Bronze (ORC + MinIO) → Silver (ClickHouse) → Gold (ClickHouse) → Data Quality Validation

Apache Airflow orchestrates the Silver transformations, Gold models, and automated validation.

## Technology Stack

- Python — ingestion and transformations
- MinIO — Bronze object storage
- Apache ORC — columnar file format
- ClickHouse — analytical database
- Apache Airflow — pipeline orchestration
- PostgreSQL — Airflow metadata
- Docker Compose — containerized infrastructure

## Data Pipeline

### Bronze
- 10 synthetic wealth-management datasets
- 210 partitioned ORC files
- MinIO object storage
- External ClickHouse S3 tables

### Silver
10 transformed datasets:
- Clients
- Accounts
- Portfolios
- Securities
- Holdings
- Transactions
- Trades
- Advisors
- Fees
- Statements

Includes SQL and Python transformations, staging-table validation, and historical client-data modeling experiments.

### Gold
Three analytics-ready tables:
- `gold_account_activity`
- `gold_portfolio_holdings`
- `gold_statement_summary`

## Airflow DAG

DAG ID: `wealth_management_silver_gold`

Execution sequence:

1. `run_silver_sql_pipeline`
2. `run_silver_python_pipeline`
3. `run_gold_pipeline`
4. `validate_data_quality`

The DAG runs manually and prevents overlapping DAG runs.

## Data Quality

Automated checks include:
- Expected row counts
- Composite-key uniqueness
- Financial reconciliation

Validated results:
- 10 Silver tables passed
- 3 Gold tables passed
- Financial reconciliation passed
- Complete Airflow DAG executed successfully on November 2, 2026

## Local Setup

1. Clone the repository.
2. Copy `.env.example` to `.env`.
3. Configure local credentials in `.env`.
4. Start the infrastructure:

   docker compose up -d --build

5. Access Airflow at http://localhost:8080.
6. Prepare source data and Bronze ORC files.
7. Upload Bronze objects to MinIO.
8. Initialize Bronze ClickHouse tables.
9. Trigger `wealth_management_silver_gold` in Airflow.

Source data is not included in this repository. The project requires the prepared synthetic datasets and Bronze objects for a complete run.

## Useful Commands

Validate Docker configuration:

    docker compose config --quiet

Check containers:

    docker compose ps

Trigger the pipeline:

    docker exec de_airflow_scheduler airflow dags trigger wealth_management_silver_gold

Check pipeline status:

    docker exec de_airflow_scheduler airflow dags list-runs -d wealth_management_silver_gold

## Security and Limitations

- Local credentials are stored in `.env`, which is excluded from Git.
- `.env.example` documents required configuration variables.
- Bronze SQL uses credential placeholders resolved by the initialization script.
- Existing ClickHouse S3 table definitions may retain credentials in database metadata.
- Expected row counts reflect the current synthetic dataset.
- Gold financial amounts are not normalized across currencies.
- This is a local development and portfolio project, not a production deployment.

## Project Status

Core Silver-to-Gold orchestration and automated data-quality validation completed successfully.

## DATA-2: Incremental Data Ingestion & CDC

DATA-2 extends the Medallion Pipeline Engine with simulated
Change Data Capture (CDC) for wealth management client records.

### Features

- Maintains a current-state client table using ClickHouse ReplacingMergeTree.
- Processes simulated INSERT, UPDATE, and DELETE events.
- Preserves historical client snapshots in the original Silver table.
- Uses event IDs and version numbers to support replay-safe processing.
- Supports partial updates and soft deletes.
- Orchestrates CDC processing and validation through Apache Airflow.
- Performs automated data-quality checks.

### CDC Pipeline

1. `client_cdc_events` stores incoming simulated change events.
2. `process_client_cdc.py` processes unhandled events.
3. `silver_clients_current` maintains the latest client state.
4. `client_cdc_processed_events` tracks processed event IDs.
5. `validate_client_cdc.py` validates the resulting data.

### Airflow DAG

DAG: `wealth_management_client_cdc`

Tasks:

1. `process_client_changes`
2. `validate_client_changes`

### Verified Results

- 3 simulated CDC events processed successfully.
- INSERT, UPDATE, and DELETE operations verified.
- 31 client keys maintained, including 1 soft-deleted client.
- 0 pending events and 0 duplicate current-client keys.
- Repeated execution applied 0 additional events.
- Both Airflow tasks completed successfully.

### Limitations

This is a simulated batch CDC prototype, not a live database
change-streaming implementation. Production improvements would
include stronger event ordering, transactional checkpointing,
concurrency controls, and comprehensive reconciliation.

## DATA-3: Data Quality, Monitoring & Observability

Implemented historical data-quality and pipeline execution monitoring using Apache Airflow, Python, and ClickHouse.

### Monitoring Features

- Automated row-count and duplicate-key checks across 13 Silver and Gold tables.
- Financial reconciliation validation.
- CDC pending-event and duplicate-key monitoring.
- Shared run IDs connecting quality metrics to pipeline executions.
- Airflow success and failure callbacks.
- Pipeline execution duration tracking.
- Persistent monitoring history in ClickHouse.

### Monitoring Tables

- monitoring.data_quality_metrics
- monitoring.pipeline_runs

### Verified Results

| Pipeline | Status | Duration | Quality Checks |
|----------|--------|----------|----------------|
| DATA-1 Silver/Gold | Success | 23.87 seconds | 28 passed |
| DATA-2 Client CDC | Success | 5.12 seconds | 2 passed |

### Monitoring Setup

Run the monitoring SQL schema using:

    docker exec -i de_clickhouse clickhouse-client --multiquery < sql/monitoring/create_monitoring_tables.sql

### Limitations

- CDC uses simulated batch events rather than live streaming.
- Monitoring records DAG execution results, not individual task durations.
- A visual monitoring dashboard is not yet implemented.
- Failure callbacks have not yet been tested against an intentionally failed DAG run.
