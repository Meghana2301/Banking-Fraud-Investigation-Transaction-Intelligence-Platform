-- SQLite-compatible analytical examples. Run after python -m src.pipeline.
-- Daily transaction volume and value
SELECT substr(timestamp,1,10) AS transaction_date,
       COUNT(*) AS transaction_count,
       ROUND(SUM(amount),2) AS transaction_value,
       SUM(flagged) AS flagged_count
FROM transactions
GROUP BY substr(timestamp,1,10)
ORDER BY transaction_date;

-- Flag rate by channel
SELECT channel, COUNT(*) AS transactions,
       ROUND(100.0 * SUM(flagged) / NULLIF(COUNT(*),0),2) AS flagged_pct
FROM transactions GROUP BY channel ORDER BY flagged_pct DESC;

-- Top customers by total transaction value (window function)
WITH customer_totals AS (
 SELECT customer_id, SUM(amount) AS total_amount FROM transactions GROUP BY customer_id
)
SELECT customer_id, ROUND(total_amount,2) AS total_amount,
       DENSE_RANK() OVER (ORDER BY total_amount DESC) AS value_rank
FROM customer_totals ORDER BY value_rank LIMIT 20;

-- Basic reconciliation
SELECT COUNT(*) AS transaction_count,
       SUM(CASE WHEN flagged=1 THEN 1 ELSE 0 END) AS flagged_count,
       SUM(CASE WHEN flagged=0 THEN 1 ELSE 0 END) AS unflagged_count
FROM transactions;
