
-- DATA-1: Silver transactions full refresh
-- Local development only; TRUNCATE + INSERT is not atomic.

CREATE TABLE IF NOT EXISTS wealth_management.silver_transactions
(
    organisation_id String,
    transaction_id String,
    account_id String,
    transaction_type Nullable(String),
    amount Nullable(Float64),
    currency Nullable(String),
    processing_date Date,
    ingested_at DateTime DEFAULT now()
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(processing_date)
ORDER BY (organisation_id, transaction_id, processing_date);

TRUNCATE TABLE wealth_management.silver_transactions;

INSERT INTO wealth_management.silver_transactions
(
    organisation_id,
    transaction_id,
    account_id,
    transaction_type,
    amount,
    currency,
    processing_date
)
SELECT
    organisation_id,
    transaction_id,
    account_id,
    transaction_type,
    amount,
    currency,
    toDate(processing_date)
FROM
(
    SELECT
        assumeNotNull(organisation_id) AS organisation_id,
        assumeNotNull(transaction_id) AS transaction_id,
        assumeNotNull(account_id) AS account_id,
        transaction_type,
        amount,
        currency,
        assumeNotNull(processing_date) AS processing_date,
        row_number() OVER (
            PARTITION BY
                organisation_id,
                transaction_id,
                processing_date
            ORDER BY
                account_id,
                transaction_type,
                amount,
                currency
        ) AS row_num
    FROM wealth_management.bronze_transactions
    WHERE organisation_id IS NOT NULL
      AND transaction_id IS NOT NULL
      AND account_id IS NOT NULL
      AND processing_date IS NOT NULL
      AND match(
          assumeNotNull(processing_date),
          '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
      )
      AND isNotNull(
          parseDateTimeBestEffortOrNull(assumeNotNull(processing_date))
      )
)
WHERE row_num = 1;
