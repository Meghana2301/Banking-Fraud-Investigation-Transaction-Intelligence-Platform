
WITH staging_totals AS (
    SELECT
        COUNT(*) AS total_transactions,
        COUNT_IF(FLAGGED = 1) AS total_flagged,
        COUNT_IF(IS_FRAUD = 1) AS total_labeled_fraud,
        SUM(AMOUNT) AS total_amount
    FROM {{ ref('stg_transactions') }}
),

daily_totals AS (
    SELECT
        SUM(TOTAL_TRANSACTIONS) AS total_transactions,
        SUM(FLAGGED_TRANSACTIONS) AS total_flagged,
        SUM(LABELED_FRAUD_TRANSACTIONS) AS total_labeled_fraud,
        SUM(TOTAL_TRANSACTION_AMOUNT) AS total_amount
    FROM {{ ref('mart_daily_transaction_intelligence') }}
)

SELECT
    s.total_transactions AS staging_transactions,
    d.total_transactions AS daily_transactions,
    s.total_flagged AS staging_flagged,
    d.total_flagged AS daily_flagged,
    s.total_labeled_fraud AS staging_fraud,
    d.total_labeled_fraud AS daily_fraud,
    s.total_amount AS staging_amount,
    d.total_amount AS daily_amount

FROM staging_totals s
CROSS JOIN daily_totals d

WHERE
    s.total_transactions IS DISTINCT FROM d.total_transactions
    OR s.total_flagged IS DISTINCT FROM d.total_flagged
    OR s.total_labeled_fraud IS DISTINCT FROM d.total_labeled_fraud
    OR s.total_amount IS DISTINCT FROM d.total_amount
