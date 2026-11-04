
-- DATA-1: Silver holdings full refresh
-- Local development only; TRUNCATE + INSERT is not atomic.

CREATE TABLE IF NOT EXISTS wealth_management.silver_holdings
(
    organisation_id String,
    holding_id String,
    portfolio_id String,
    security_id String,
    quantity Nullable(Int64),
    unit_price Nullable(Float64),
    market_value Nullable(Float64),
    processing_date Date,
    ingested_at DateTime DEFAULT now()
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(processing_date)
ORDER BY (organisation_id, holding_id, processing_date);

TRUNCATE TABLE wealth_management.silver_holdings;

INSERT INTO wealth_management.silver_holdings
(
    organisation_id,
    holding_id,
    portfolio_id,
    security_id,
    quantity,
    unit_price,
    market_value,
    processing_date
)
SELECT
    organisation_id,
    holding_id,
    portfolio_id,
    security_id,
    quantity,
    unit_price,
    market_value,
    toDate(processing_date)
FROM
(
    SELECT
        assumeNotNull(organisation_id) AS organisation_id,
        assumeNotNull(holding_id) AS holding_id,
        assumeNotNull(portfolio_id) AS portfolio_id,
        assumeNotNull(security_id) AS security_id,
        quantity,
        unit_price,
        market_value,
        assumeNotNull(processing_date) AS processing_date,
        row_number() OVER (
            PARTITION BY organisation_id, holding_id, processing_date
            ORDER BY
                portfolio_id,
                security_id,
                quantity,
                unit_price,
                market_value
        ) AS row_num
    FROM wealth_management.bronze_holdings
    WHERE organisation_id IS NOT NULL
      AND holding_id IS NOT NULL
      AND portfolio_id IS NOT NULL
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
