-- queries/monthly_active_users.sql
-- Monthly Active Users (MAU): Distinct customers with at least one transaction per month.
-- Segment breakdown by customer_type (Enterprise / SMB / Startup).
-- Covers the trailing 12 months from the current month boundary.
-- One canonical definition, reused by every team.

SELECT
    DATE_TRUNC('month', transaction_date)::DATE          AS month,
    COUNT(DISTINCT customer_id)                          AS active_users,
    COUNT(DISTINCT customer_id) FILTER (WHERE customer_type = 'Enterprise') AS enterprise_users,
    COUNT(DISTINCT customer_id) FILTER (WHERE customer_type = 'SMB')        AS smb_users,
    COUNT(DISTINCT customer_id) FILTER (WHERE customer_type = 'Startup')    AS startup_users
FROM transactions
WHERE transaction_date >= DATE_TRUNC('month', NOW()) - INTERVAL '12 months'
GROUP BY DATE_TRUNC('month', transaction_date)
ORDER BY month DESC;
