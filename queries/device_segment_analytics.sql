-- CyberGuard Threat Analytics by Device Segment Query
-- Aggregates login attempts and risk metrics grouped by device type
SELECT 
    device_type,
    COUNT(*) as total_attempts,
    SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) as failed_attempts,
    ROUND(AVG(risk_score), 2) as avg_risk_score,
    MAX(risk_score) as max_risk_score
FROM auth_events
GROUP BY device_type
ORDER BY max_risk_score DESC;
