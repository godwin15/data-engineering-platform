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
