
WITH staging_flagged AS (
    SELECT TRANSACTION_ID
    FROM {{ ref('stg_transactions') }}
    WHERE FLAGGED = 1
),

mart_flagged AS (
    SELECT TRANSACTION_ID
    FROM {{ ref('mart_high_risk_transactions') }}
),

missing_from_mart AS (
    SELECT TRANSACTION_ID
    FROM staging_flagged

    MINUS

    SELECT TRANSACTION_ID
    FROM mart_flagged
),

unexpected_in_mart AS (
    SELECT TRANSACTION_ID
    FROM mart_flagged

    MINUS

    SELECT TRANSACTION_ID
    FROM staging_flagged
)

SELECT
    'MISSING_FROM_MART' AS ISSUE,
    TRANSACTION_ID
FROM missing_from_mart

UNION ALL

SELECT
    'UNEXPECTED_IN_MART' AS ISSUE,
    TRANSACTION_ID
FROM unexpected_in_mart
