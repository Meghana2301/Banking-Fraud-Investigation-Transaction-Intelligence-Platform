
WITH staging_totals AS (
    SELECT
        COUNT(*) AS total_transactions,
        COUNT_IF(FLAGGED = 1) AS total_flagged,
        COUNT_IF(IS_FRAUD = 1) AS total_labeled_fraud,
        SUM(AMOUNT) AS total_amount
    FROM {{ ref('stg_transactions') }}
),

customer_totals AS (
    SELECT
        SUM(TOTAL_TRANSACTIONS) AS total_transactions,
        SUM(FLAGGED_TRANSACTIONS) AS total_flagged,
        SUM(LABELED_FRAUD_TRANSACTIONS) AS total_labeled_fraud,
        SUM(TOTAL_TRANSACTION_AMOUNT) AS total_amount
    FROM {{ ref('mart_customer_risk_summary') }}
)

SELECT
    s.total_transactions AS staging_transactions,
    c.total_transactions AS customer_transactions,
    s.total_flagged AS staging_flagged,
    c.total_flagged AS customer_flagged,
    s.total_labeled_fraud AS staging_fraud,
    c.total_labeled_fraud AS customer_fraud,
    s.total_amount AS staging_amount,
    c.total_amount AS customer_amount

FROM staging_totals s
CROSS JOIN customer_totals c

WHERE
    s.total_transactions IS DISTINCT FROM c.total_transactions
    OR s.total_flagged IS DISTINCT FROM c.total_flagged
    OR s.total_labeled_fraud IS DISTINCT FROM c.total_labeled_fraud
    OR s.total_amount IS DISTINCT FROM c.total_amount
