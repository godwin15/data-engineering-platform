CREATE DATABASE IF NOT EXISTS data_quality_test;

CREATE TABLE IF NOT EXISTS data_quality_test.test_clients
(
    organisation_id Nullable(String),
    client_id String,
    client_name Nullable(String),
    processing_date Date
)
ENGINE = MergeTree()
ORDER BY (client_id, processing_date);

CREATE TABLE IF NOT EXISTS data_quality_test.test_accounts
(
    organisation_id String,
    account_id String,
    client_id String,
    balance Float64,
    processing_date Date
)
ENGINE = MergeTree()
ORDER BY (organisation_id, account_id, processing_date);

TRUNCATE TABLE data_quality_test.test_accounts;
TRUNCATE TABLE data_quality_test.test_clients;

INSERT INTO data_quality_test.test_clients VALUES
('ORG001', 'C001', 'Test Client One', '2026-01-01'),
('ORG001', 'C002', 'Test Client Two', '2026-01-01'),
('ORG002', 'C003', 'Test Client Three', '2026-01-01'),
('ORG002', 'C004', 'Test Client Four', '2026-01-01');

INSERT INTO data_quality_test.test_accounts VALUES
('ORG001', 'A001', 'C001', 5000, '2026-01-01'),
('ORG001', 'A002', 'C002', 2500, '2026-01-01'),
('ORG002', 'A003', 'C003', 7500, '2026-01-01'),
('ORG002', 'A004', 'C004', 1000, '2026-01-01');
