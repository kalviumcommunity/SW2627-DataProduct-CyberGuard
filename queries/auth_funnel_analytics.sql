-- CyberGuard Authentication Funnel Query
-- Analyzes progression from Total Logins -> Successful Logins -> High Risk Events -> Critical Alerts
SELECT 
    COUNT(*) as total_logins,
    SUM(CASE WHEN status = 'Success' THEN 1 ELSE 0 END) as successful_logins,
    SUM(CASE WHEN risk_score >= 70 THEN 1 ELSE 0 END) as high_risk_events,
    SUM(CASE WHEN severity = 'CRITICAL' THEN 1 ELSE 0 END) as critical_incidents
FROM auth_events;
