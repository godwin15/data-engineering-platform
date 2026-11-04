
-- DATA-1: Silver accounts full refresh
-- Local development only; TRUNCATE + INSERT is not atomic.

CREATE TABLE IF NOT EXISTS wealth_management.silver_accounts
(
    organisation_id String,
    account_id String,
    client_id String,
    account_type Nullable(String),
    currency Nullable(String),
    opening_balance Nullable(Float64),
    processing_date Date,
    ingested_at DateTime DEFAULT now()
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(processing_date)
ORDER BY (organisation_id, account_id, processing_date);

TRUNCATE TABLE wealth_management.silver_accounts;

INSERT INTO wealth_management.silver_accounts
(
    organisation_id,
    account_id,
    client_id,
    account_type,
    currency,
    opening_balance,
    processing_date
)
SELECT
    organisation_id,
    account_id,
    client_id,
    account_type,
    currency,
    opening_balance,
    toDate(processing_date)
FROM
(
    SELECT
        assumeNotNull(organisation_id) AS organisation_id,
        assumeNotNull(account_id) AS account_id,
        assumeNotNull(client_id) AS client_id,
        account_type,
        currency,
        opening_balance,
        assumeNotNull(processing_date) AS processing_date,
        row_number() OVER (
            PARTITION BY organisation_id, account_id, processing_date
            ORDER BY client_id, account_type, currency, opening_balance
        ) AS row_num
    FROM wealth_management.bronze_accounts
    WHERE organisation_id IS NOT NULL
      AND account_id IS NOT NULL
      AND client_id IS NOT NULL
      AND processing_date IS NOT NULL
      AND match(assumeNotNull(processing_date), '^\d{4}-\d{2}-\d{2}$')
      AND isNotNull(
          parseDateTimeBestEffortOrNull(assumeNotNull(processing_date))
      )
)
WHERE row_num = 1;
