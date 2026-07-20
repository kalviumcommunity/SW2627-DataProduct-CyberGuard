-- queries/revenue_by_segment.sql
-- Revenue by Customer Segment: monthly revenue metrics broken down by customer_type.
-- Joins transactions with customers to enrich with segment metadata.
-- 4 core metrics: order_count, monthly_revenue, avg_order_value, unique_customers, revenue_per_customer.
-- One canonical definition – no more "Finance vs Sales vs Product" revenue discrepancies.

SELECT
    c.customer_type,
    DATE_TRUNC('month', t.transaction_date)::DATE        AS month,
    COUNT(DISTINCT t.order_id)                           AS order_count,
    SUM(t.amount)                                        AS monthly_revenue,
    ROUND(AVG(t.amount), 2)                              AS avg_order_value,
    COUNT(DISTINCT t.customer_id)                        AS unique_customers,
    ROUND(SUM(t.amount) / COUNT(DISTINCT t.customer_id), 2) AS revenue_per_customer
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.transaction_date >= DATE_TRUNC('month', NOW()) - INTERVAL '12 months'
GROUP BY c.customer_type, DATE_TRUNC('month', t.transaction_date)
ORDER BY month DESC, monthly_revenue DESC;
