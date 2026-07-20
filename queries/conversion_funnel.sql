-- queries/conversion_funnel.sql
-- Conversion Funnel: daily signup → email verification → first purchase pipeline.
-- Uses FILTER (WHERE ...) for conditional counting in a single scan.
-- Covers the trailing 90 days to give a meaningful conversion window.
-- conversion_pct = percentage of sign-ups who completed their first purchase.

SELECT
    DATE_TRUNC('day', u.created_at)::DATE                             AS signup_date,
    COUNT(*)                                                          AS signups,
    COUNT(*) FILTER (WHERE u.email_verified_at IS NOT NULL)           AS email_verified,
    COUNT(*) FILTER (WHERE u.first_purchase_at IS NOT NULL)           AS first_purchase,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE u.first_purchase_at IS NOT NULL)
              / NULLIF(COUNT(*), 0),
        1
    )                                                                 AS conversion_pct
FROM users u
WHERE u.created_at >= NOW() - INTERVAL '90 days'
GROUP BY DATE_TRUNC('day', u.created_at)
ORDER BY signup_date DESC;
