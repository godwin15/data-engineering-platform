
-- DATA-1: Silver Layer
-- SCD Type 2 client history
-- Rebuild from controlled test snapshots
-- For local development and testing only

CREATE TABLE IF NOT EXISTS wealth_management.silver_clients_history
(
    organisation_id String,
    client_id String,
    client_name String,
    email Nullable(String),
    country Nullable(String),
    risk_profile Nullable(String),
    account_status Nullable(String),
    valid_from Date,
    valid_to Nullable(Date),
    is_current UInt8
)
ENGINE = MergeTree()
ORDER BY (organisation_id, client_id, valid_from);

-- Refresh history so repeated execution does not append duplicates
TRUNCATE TABLE wealth_management.silver_clients_history;

INSERT INTO wealth_management.silver_clients_history
WITH snapshots AS
(
    SELECT
        organisation_id,
        client_id,
        client_name,
        email,
        country,
        risk_profile,
        account_status,
        processing_date,
        lagInFrame(
            tuple(client_name, email, country, risk_profile, account_status),
            1,
            tuple(client_name, email, country, risk_profile, account_status)
        ) OVER (
            PARTITION BY organisation_id, client_id
            ORDER BY processing_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS previous_attributes,
        row_number() OVER (
            PARTITION BY organisation_id, client_id
            ORDER BY processing_date
        ) AS snapshot_number
    FROM wealth_management.silver_clients_scd_test
),
changes AS
(
    SELECT
        organisation_id,
        client_id,
        client_name,
        email,
        country,
        risk_profile,
        account_status,
        processing_date AS valid_from
    FROM snapshots
    WHERE snapshot_number = 1
       OR tuple(client_name, email, country, risk_profile, account_status)
          != previous_attributes
)
SELECT
    organisation_id,
    client_id,
    client_name,
    email,
    country,
    risk_profile,
    account_status,
    valid_from,
    leadInFrame(
        toNullable(valid_from),
        1,
        CAST(NULL, 'Nullable(Date)')
    ) OVER (
        PARTITION BY organisation_id, client_id
        ORDER BY valid_from
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) AS valid_to,
    if(isNull(valid_to), 1, 0) AS is_current
FROM changes;
