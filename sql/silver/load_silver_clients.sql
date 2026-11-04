
-- DATA-1: Silver clients refresh
-- Local development: rebuild from validated Bronze snapshots.
-- TRUNCATE + INSERT is not atomic; do not use this approach
-- for concurrent production readers.

TRUNCATE TABLE wealth_management.silver_clients;

INSERT INTO wealth_management.silver_clients
(
    organisation_id,
    client_id,
    client_name,
    email,
    country,
    risk_profile,
    account_status,
    processing_date
)
SELECT
    organisation_id,
    client_id,
    client_name,
    email,
    country,
    risk_profile,
    account_status,
    toDate(processing_date)
FROM
(
    SELECT
        assumeNotNull(organisation_id) AS organisation_id,
        assumeNotNull(client_id) AS client_id,
        assumeNotNull(client_name) AS client_name,
        email,
        country,
        risk_profile,
        account_status,
        assumeNotNull(processing_date) AS processing_date,
        row_number() OVER (
            PARTITION BY
                organisation_id,
                client_id,
                processing_date
            ORDER BY
                client_name,
                email,
                country,
                risk_profile,
                account_status
        ) AS row_num
    FROM wealth_management.bronze_clients
    WHERE
        organisation_id IS NOT NULL
        AND client_id IS NOT NULL
        AND client_name IS NOT NULL
        AND processing_date IS NOT NULL
        AND match(
            assumeNotNull(processing_date),
            '^\\d{4}-\\d{2}-\\d{2}$'
        )
        AND isNotNull(
            parseDateTimeBestEffortOrNull(
                assumeNotNull(processing_date)
            )
        )
)
WHERE row_num = 1;
