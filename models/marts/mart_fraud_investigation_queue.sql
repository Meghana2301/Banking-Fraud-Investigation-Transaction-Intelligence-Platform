
{{ config(materialized='view', schema='MARTS') }}

SELECT
    t.TRANSACTION_ID,
    t.CUSTOMER_ID,
    t.ACCOUNT_ID,
    t.TRANSACTION_TIMESTAMP,
    t.AMOUNT,
    t.MERCHANT_CATEGORY,
    t.COUNTRY,
    t.CHANNEL,
    t.RISK_SCORE,
    t.RISK_LEVEL,
    c.CUSTOMER_RISK_LEVEL,
    c.TOTAL_TRANSACTIONS,
    c.FLAGGED_TRANSACTIONS AS CUSTOMER_FLAGGED_COUNT,

    CASE
        WHEN t.RISK_SCORE >= 80
             AND c.FLAGGED_TRANSACTIONS >= 2
            THEN 'P1 - URGENT'

        WHEN t.RISK_SCORE >= 80
            THEN 'P2 - HIGH'

        WHEN c.FLAGGED_TRANSACTIONS >= 2
            THEN 'P2 - HIGH'

        ELSE 'P3 - REVIEW'
    END AS INVESTIGATION_PRIORITY

FROM {{ ref('mart_high_risk_transactions') }} t

LEFT JOIN {{ ref('mart_customer_risk_summary') }} c
    ON t.CUSTOMER_ID = c.CUSTOMER_ID
