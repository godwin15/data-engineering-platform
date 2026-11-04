
-- DATA-1: Bronze Layer
-- External ClickHouse tables reading ORC files from MinIO

CREATE DATABASE IF NOT EXISTS wealth_management;

CREATE TABLE IF NOT EXISTS wealth_management.bronze_clients
ENGINE = S3(
    'http://minio:9000/wealth-management-bronze/clients/organisation_id=*/processing_date=*/data.orc',
    '__MINIO_ACCESS_KEY__', '__MINIO_SECRET_KEY__', 'ORC'
);

CREATE TABLE IF NOT EXISTS wealth_management.bronze_accounts
ENGINE = S3(
    'http://minio:9000/wealth-management-bronze/accounts/organisation_id=*/processing_date=*/data.orc',
    '__MINIO_ACCESS_KEY__', '__MINIO_SECRET_KEY__', 'ORC'
);

CREATE TABLE IF NOT EXISTS wealth_management.bronze_portfolios
ENGINE = S3(
    'http://minio:9000/wealth-management-bronze/portfolios/organisation_id=*/processing_date=*/data.orc',
    '__MINIO_ACCESS_KEY__', '__MINIO_SECRET_KEY__', 'ORC'
);

CREATE TABLE IF NOT EXISTS wealth_management.bronze_securities
ENGINE = S3(
    'http://minio:9000/wealth-management-bronze/securities/organisation_id=*/processing_date=*/data.orc',
    '__MINIO_ACCESS_KEY__', '__MINIO_SECRET_KEY__', 'ORC'
);

CREATE TABLE IF NOT EXISTS wealth_management.bronze_holdings
ENGINE = S3(
    'http://minio:9000/wealth-management-bronze/holdings/organisation_id=*/processing_date=*/data.orc',
    '__MINIO_ACCESS_KEY__', '__MINIO_SECRET_KEY__', 'ORC'
);

CREATE TABLE IF NOT EXISTS wealth_management.bronze_transactions
ENGINE = S3(
    'http://minio:9000/wealth-management-bronze/transactions/organisation_id=*/processing_date=*/data.orc',
    '__MINIO_ACCESS_KEY__', '__MINIO_SECRET_KEY__', 'ORC'
);

CREATE TABLE IF NOT EXISTS wealth_management.bronze_trades
ENGINE = S3(
    'http://minio:9000/wealth-management-bronze/trades/organisation_id=*/processing_date=*/data.orc',
    '__MINIO_ACCESS_KEY__', '__MINIO_SECRET_KEY__', 'ORC'
);

CREATE TABLE IF NOT EXISTS wealth_management.bronze_advisors
ENGINE = S3(
    'http://minio:9000/wealth-management-bronze/advisors/organisation_id=*/processing_date=*/data.orc',
    '__MINIO_ACCESS_KEY__', '__MINIO_SECRET_KEY__', 'ORC'
);

CREATE TABLE IF NOT EXISTS wealth_management.bronze_fees
ENGINE = S3(
    'http://minio:9000/wealth-management-bronze/fees/organisation_id=*/processing_date=*/data.orc',
    '__MINIO_ACCESS_KEY__', '__MINIO_SECRET_KEY__', 'ORC'
);

CREATE TABLE IF NOT EXISTS wealth_management.bronze_statements
ENGINE = S3(
    'http://minio:9000/wealth-management-bronze/statements/organisation_id=*/processing_date=*/data.orc',
    '__MINIO_ACCESS_KEY__', '__MINIO_SECRET_KEY__', 'ORC'
);
