
-- DATA-1: Silver portfolios full refresh
-- Local development only; TRUNCATE + INSERT is not atomic.

CREATE TABLE IF NOT EXISTS wealth_management.silver_portfolios
(
    organisation_id String,
    portfolio_id String,
    account_id String,
    portfolio_name Nullable(String),
    investment_strategy Nullable(String),
    base_currency Nullable(String),
    processing_date Date,
    ingested_at DateTime DEFAULT now()
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(processing_date)
ORDER BY (organisation_id, portfolio_id, processing_date);

TRUNCATE TABLE wealth_management.silver_portfolios;

INSERT INTO wealth_management.silver_portfolios
(
    organisation_id,
    portfolio_id,
    account_id,
    portfolio_name,
    investment_strategy,
    base_currency,
    processing_date
)
SELECT
    organisation_id,
    portfolio_id,
    account_id,
    portfolio_name,
    investment_strategy,
    base_currency,
    toDate(processing_date)
FROM
(
    SELECT
        assumeNotNull(organisation_id) AS organisation_id,
        assumeNotNull(portfolio_id) AS portfolio_id,
        assumeNotNull(account_id) AS account_id,
        portfolio_name,
        investment_strategy,
        base_currency,
        assumeNotNull(processing_date) AS processing_date,
        row_number() OVER (
            PARTITION BY organisation_id, portfolio_id, processing_date
            ORDER BY account_id, portfolio_name, investment_strategy, base_currency
        ) AS row_num
    FROM wealth_management.bronze_portfolios
    WHERE organisation_id IS NOT NULL
      AND portfolio_id IS NOT NULL
      AND account_id IS NOT NULL
      AND processing_date IS NOT NULL
      AND match(assumeNotNull(processing_date), '^\d{4}-\d{2}-\d{2}$')
      AND isNotNull(
          parseDateTimeBestEffortOrNull(assumeNotNull(processing_date))
      )
)
WHERE row_num = 1;
