
WITH high_risk AS (
    SELECT TRANSACTION_ID
    FROM {{ ref('mart_high_risk_transactions') }}
),

investigation_queue AS (
    SELECT TRANSACTION_ID
    FROM {{ ref('mart_fraud_investigation_queue') }}
),

missing_from_queue AS (
    SELECT TRANSACTION_ID
    FROM high_risk

    MINUS

    SELECT TRANSACTION_ID
    FROM investigation_queue
),

unexpected_in_queue AS (
    SELECT TRANSACTION_ID
    FROM investigation_queue

    MINUS

    SELECT TRANSACTION_ID
    FROM high_risk
),

duplicate_queue_ids AS (
    SELECT TRANSACTION_ID
    FROM investigation_queue
    GROUP BY TRANSACTION_ID
    HAVING COUNT(*) > 1
)

SELECT
    'MISSING_FROM_QUEUE' AS ISSUE,
    TRANSACTION_ID
FROM missing_from_queue

UNION ALL

SELECT
    'UNEXPECTED_IN_QUEUE' AS ISSUE,
    TRANSACTION_ID
FROM unexpected_in_queue

UNION ALL

SELECT
    'DUPLICATE_IN_QUEUE' AS ISSUE,
    TRANSACTION_ID
FROM duplicate_queue_ids
