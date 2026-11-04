
-- DATA-1: Silver securities full refresh
-- Local development only; TRUNCATE + INSERT is not atomic.

CREATE TABLE IF NOT EXISTS wealth_management.silver_securities
(
    organisation_id String,
    security_id String,
    security_name Nullable(String),
    ticker Nullable(String),
    asset_type Nullable(String),
    currency Nullable(String),
    processing_date Date,
    ingested_at DateTime DEFAULT now()
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(processing_date)
ORDER BY (organisation_id, security_id, processing_date);

TRUNCATE TABLE wealth_management.silver_securities;

INSERT INTO wealth_management.silver_securities
(
    organisation_id,
    security_id,
    security_name,
    ticker,
    asset_type,
    currency,
    processing_date
)
SELECT
    organisation_id,
    security_id,
    security_name,
    ticker,
    asset_type,
    currency,
    toDate(processing_date)
FROM
(
    SELECT
        assumeNotNull(organisation_id) AS organisation_id,
        assumeNotNull(security_id) AS security_id,
        security_name,
        ticker,
        asset_type,
        currency,
        assumeNotNull(processing_date) AS processing_date,
        row_number() OVER (
            PARTITION BY organisation_id, security_id, processing_date
            ORDER BY security_name, ticker, asset_type, currency
        ) AS row_num
    FROM wealth_management.bronze_securities
    WHERE organisation_id IS NOT NULL
      AND security_id IS NOT NULL
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
