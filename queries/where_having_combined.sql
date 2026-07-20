-- queries/where_having_combined.sql
-- Task 4: WHERE + HAVING Combined -- Real-World Operational Reporting
--
-- Production queries almost always need BOTH:
--   WHERE  → strip invalid / out-of-scope rows (data quality + date range)
--   HAVING → enforce business-rule thresholds on aggregated segments
--
-- SQL execution order (logical):
--   1. FROM  / JOIN   -- identify source tables
--   2. WHERE          -- filter individual rows   ← WHERE lives here
--   3. GROUP BY       -- form groups
--   4. HAVING         -- filter groups            ← HAVING lives here
--   5. SELECT         -- compute output columns
--   6. ORDER BY       -- sort
--   7. LIMIT          -- cap result set
--
-- Business logic documented inline:
--   WHERE t.transaction_date >= '2024-01-01'   -- analysis window: current year
--   WHERE t.transaction_status = 'completed'   -- data quality: no failed/pending
--   WHERE t.amount > 0                         -- logical validity: no refunds
--   HAVING COUNT(DISTINCT t.customer_id) >= 100 -- segment size: statistically significant
--   HAVING SUM(t.amount) > 100000              -- business threshold: material segments only

SELECT
    c.customer_type,
    COUNT(DISTINCT t.customer_id)        AS segment_customers,
    COUNT(*)                             AS order_count,
    SUM(t.amount)                        AS segment_revenue,
    ROUND(AVG(t.amount), 2)              AS avg_order_value,
    ROUND(
        100.0 * SUM(t.amount)
              / SUM(SUM(t.amount)) OVER (),
        2
    )                                    AS revenue_share_pct   -- % of grand total
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.transaction_date >= DATE '2024-01-01'       -- WHERE: restrict analysis window
  AND t.transaction_status = 'completed'            -- WHERE: data quality guard
  AND t.amount > 0                                  -- WHERE: logical validity
GROUP BY c.customer_type
HAVING COUNT(DISTINCT t.customer_id) >= 100         -- HAVING: ignore tiny segments
   AND SUM(t.amount) > 100000                       -- HAVING: material revenue only
ORDER BY segment_revenue DESC;
