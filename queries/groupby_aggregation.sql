-- queries/groupby_aggregation.sql
-- Task 2: GROUP BY and Aggregation on Multiple Dimensions
--
-- GROUP BY changes the unit of analysis from individual rows to groups.
-- The SELECT list must contain only:
--   a) columns listed in GROUP BY, OR
--   b) aggregate expressions (COUNT, SUM, AVG, MIN, MAX).
--
-- WHERE fires BEFORE GROUP BY:  rows that fail the WHERE predicate never
-- enter any group, which is more efficient than filtering after aggregation.
--
-- Here we slice revenue by two dimensions: customer_type × month.
-- Three aggregate functions: COUNT(DISTINCT), COUNT(*), SUM, AVG.

SELECT
    c.customer_type,
    DATE_TRUNC('month', t.transaction_date)::DATE  AS month,
    COUNT(DISTINCT t.customer_id)                  AS unique_customers,
    COUNT(*)                                       AS transaction_count,
    SUM(t.amount)                                  AS monthly_revenue,
    ROUND(AVG(t.amount), 2)                        AS avg_transaction
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.transaction_date >= DATE '2024-01-01'   -- WHERE filters rows FIRST (faster)
  AND t.transaction_status = 'completed'        -- Only count completed transactions
GROUP BY c.customer_type,
         DATE_TRUNC('month', t.transaction_date) -- Two-dimensional grouping
ORDER BY month DESC, monthly_revenue DESC;
