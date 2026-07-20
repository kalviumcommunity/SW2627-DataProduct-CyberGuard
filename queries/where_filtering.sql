-- queries/where_filtering.sql
-- Task 1: WHERE Filtering -- Data Quality Checks BEFORE Grouping
--
-- WHERE filters individual ROWS before any grouping or aggregation happens.
-- Use it to exclude invalid, incomplete, or out-of-scope records so that
-- only clean, relevant data enters the aggregation pipeline.
--
-- Rule of thumb:
--   Use WHERE for: date ranges, status flags, logical validity (amount > 0),
--                  column-level data-quality guards.
--   Never use WHERE on aggregated expressions (SUM, COUNT, AVG) -- use HAVING.

SELECT
    customer_id,
    COUNT(*)           AS transaction_count,
    SUM(amount)        AS annual_revenue,
    ROUND(AVG(amount), 2) AS avg_transaction_value
FROM transactions
WHERE transaction_date >= DATE '2024-01-01'      -- Restrict to current analysis year
  AND transaction_date <  DATE '2025-01-01'      -- Upper boundary: exclude future rows
  AND amount > 0                                 -- Remove refunds / zero-value rows
  AND transaction_status = 'completed'           -- Valid transactions only; skip pending/failed
GROUP BY customer_id
ORDER BY annual_revenue DESC;
