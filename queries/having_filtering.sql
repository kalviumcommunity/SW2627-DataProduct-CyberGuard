-- queries/having_filtering.sql
-- Task 3: HAVING Filtering -- Group-Level Thresholds AFTER Aggregation
--
-- HAVING operates on GROUPS (post-aggregation). It is the only way to apply
-- a condition on the result of an aggregate function such as SUM or COUNT.
--
-- Difference at a glance:
--   WHERE  → filters ROWS  before groups are formed  (column-level data)
--   HAVING → filters GROUPS after aggregation        (metric-level thresholds)
--
-- Example decision:
--   "Remove transactions below $10"   → WHERE amount >= 10      (row-level fact)
--   "Show only customers who spent >$10k total" → HAVING SUM(amount) > 10000
--      (group-level metric; the individual rows all stay in the aggregation)
--
-- When to use HAVING:
--   • Business threshold: segment revenue > $100k
--   • Activity threshold: customer has 5+ purchases (engagement filter)
--   • Quality gate:       cohort has enough members to be statistically valid

SELECT
    customer_id,
    COUNT(*)       AS transaction_count,
    SUM(amount)    AS annual_revenue
FROM transactions
WHERE transaction_date >= DATE '2024-01-01'   -- Row filter: valid date range
GROUP BY customer_id
HAVING SUM(amount)  > 10000                  -- HAVING: only high-value customers
   AND COUNT(*)    >= 5                      -- HAVING: only engaged customers (5+ purchases)
ORDER BY annual_revenue DESC;
