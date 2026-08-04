-- queries/orderby_ranking.sql
-- CyberGuard Security Risk ORDER BY Ranking Query
--
-- ORDER BY controls output sort order; combined with RANK() and DENSE_RANK() window functions
-- it assigns a competitive risk rank to each user account without collapsing rows.
--
-- Key clauses used:
--   ORDER BY max_risk_score DESC  -- highest risk score first
--   LIMIT 20                      -- cap to top 20 risky users
--   RANK() OVER (ORDER BY MAX(risk_score) DESC) -- assigns 1,2,3... with ties sharing rank
--   DENSE_RANK() OVER (ORDER BY COUNT(*) DESC) -- assigns dense rank by activity volume
--
-- HAVING ensures only users with 3+ authentication attempts are ranked,
-- preventing single isolated events from polluting the security leaderboard.

SELECT
    username,
    COUNT(*)                                                        AS total_attempts,
    SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END)              AS failed_attempts,
    ROUND(AVG(risk_score), 2)                                       AS avg_risk_score,
    MAX(risk_score)                                                 AS max_risk_score,
    RANK()       OVER (ORDER BY MAX(risk_score) DESC)              AS risk_rank,
    DENSE_RANK() OVER (ORDER BY COUNT(*) DESC)                      AS volume_rank
FROM auth_events
WHERE timestamp >= '2026-07-01'
GROUP BY username
HAVING COUNT(*) >= 3
ORDER BY max_risk_score DESC
LIMIT 20;
