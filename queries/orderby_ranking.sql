-- queries/orderby_ranking.sql
-- Task 5: ORDER BY Ranking -- Surface Top Performers
--
-- ORDER BY controls output sort order; combined with RANK() window function
-- it assigns a competitive rank to each group without collapsing rows.
--
-- Key clauses used:
--   ORDER BY total_revenue DESC  -- highest revenue first
--   LIMIT 20                     -- cap to top 20 segments
--   RANK() OVER (ORDER BY SUM(t.amount) DESC) -- assigns 1,2,3... with ties sharing rank
--
-- RANK() vs ROW_NUMBER() vs DENSE_RANK():
--   RANK()       → 1,2,2,4  (gap after tie)
--   DENSE_RANK() → 1,2,2,3  (no gap)
--   ROW_NUMBER() → 1,2,3,4  (always unique)
--
-- HAVING ensures only segments with 10+ customers are ranked,
-- preventing tiny cohorts from polluting the leaderboard.

SELECT
    c.customer_type,
    COUNT(DISTINCT t.customer_id)               AS customers,
    COUNT(*)                                    AS total_orders,
    SUM(t.amount)                               AS total_revenue,
    ROUND(AVG(t.amount), 2)                     AS avg_order,
    RANK()   OVER (ORDER BY SUM(t.amount) DESC) AS revenue_rank,
    DENSE_RANK() OVER (ORDER BY COUNT(DISTINCT t.customer_id) DESC) AS customer_count_rank
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.transaction_date >= DATE '2024-01-01'    -- Current analysis window
  AND t.transaction_status = 'completed'         -- Completed transactions only
  AND t.amount > 0                               -- Exclude refunds
GROUP BY c.customer_type
HAVING COUNT(DISTINCT t.customer_id) >= 10       -- Minimum cohort for meaningful rank
ORDER BY total_revenue DESC
LIMIT 20;   -- Top 20 segments only
