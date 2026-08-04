# CyberGuard Cybersecurity Data Dictionary

## Dataset Overview
This dataset contains high-volume enterprise authentication attempt telemetry and risk analytics generated and processed in real time by the CyberGuard SOC Platform.
- **Maintained By**: CyberGuard Security Data Engineering & SOC Operations Team
- **Primary Fact Table**: `auth_events`
- **Normalized Tables**: `users`, `devices`, `risk_alerts`
- **Analytical Views**: `v_user_risk_summary`, `v_threat_timeline`

---

## Field Specifications & Definitions

### `event_id`
- **Data Type**: Integer (Primary Key, Auto-increment)
- **Business Meaning**: Unique identifier for each authentication attempt event.
- **Example**: `1042`
- **Null Handling**: Never Null.

### `timestamp`
- **Data Type**: Datetime (ISO-8601 Format `YYYY-MM-DD HH:MM:SS`)
- **Business Meaning**: Precise timestamp when the connection request hit the authentication server.
- **Example**: `2026-07-01 13:39:45`
- **Null Handling**: Coerced to valid datetime; rows with unparseable timestamps are dropped during ETL.
- **Related KPI**: Authentication velocity, temporal anomaly detection, 10-minute rolling failure windows.

### `username`
- **Data Type**: String
- **Business Meaning**: Account identifier associated with the login attempt.
- **Example**: `user_16` or `root`
- **Null Handling**: Imputed to `"unknown_user"` if missing.
- **Related KPI**: User risk profiling, brute force target analysis, privilege escalation tracking.

### `ip_address`
- **Data Type**: String (IPv4 Format)
- **Business Meaning**: Originating IP address of the client connection.
- **Example**: `185.220.101.5`
- **Null Handling**: Imputed to `"0.0.0.0"` if missing.
- **Related KPI**: IP-level failure velocity, credential stuffing source tracking, perimeter firewall blocking.

### `country`
- **Data Type**: String (ISO 2-letter Country Code)
- **Business Meaning**: Geolocation country code derived from originating IP address.
- **Example**: `IN`, `US`, `RU`, `JP`
- **Null Handling**: Imputed to `"UNKNOWN"` if missing.
- **Related KPI**: Geographic risk heatmaps, Impossible Travel velocity calculation.

### `city`
- **Data Type**: String
- **Business Meaning**: Geolocation city name resolved from IP address.
- **Example**: `Tokyo`, `San Francisco`, `Moscow`
- **Null Handling**: Imputed to `"Unknown"` if missing.

### `latitude`
- **Data Type**: Float
- **Business Meaning**: Geographic latitude coordinate (-90.0 to +90.0).
- **Example**: `37.7749`
- **Null Handling**: Imputed to `0.0`.

### `longitude`
- **Data Type**: Float
- **Business Meaning**: Geographic longitude coordinate (-180.0 to +180.0).
- **Example**: `-122.4194`
- **Null Handling**: Imputed to `0.0`.

### `status`
- **Data Type**: String (`Success` or `Failed`)
- **Business Meaning**: Binary outcome of the authentication attempt.
- **Example**: `Failed`
- **Null Handling**: Standardized to `Success` or `Failed` (fail-closed).
- **Related KPI**: Overall failure rate %, brute force burst detection.

### `device_type`
- **Data Type**: String
- **Business Meaning**: Operating system and hardware platform category.
- **Valid Values**: `Workstation-Windows`, `Laptop-macOS`, `Server-Linux`, `Mobile-iOS`, `Mobile-Android`
- **Example**: `Laptop-macOS`
- **Null Handling**: Imputed to `"Unknown-Device"`.
- **Related KPI**: Device type risk profiling, unauthorized device detection.

### `user_agent`
- **Data Type**: String
- **Business Meaning**: Full HTTP User-Agent header string sent by the client browser or script.
- **Example**: `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36`

### `threat_vector`
- **Data Type**: String
- **Business Meaning**: Primary heuristic threat tag assigned by the Threat Rule Engine.
- **Valid Values**: `Impossible Travel`, `Brute Force`, `Credential Stuffing`, `Privilege Escalation`, or `None`
- **Example**: `Impossible Travel, Brute Force`

### `anomaly_score`
- **Data Type**: Float (Range `0.0000` to `1.0000`)
- **Business Meaning**: Behavioral outlier score computed by the production Isolation Forest ML model.
- **Example**: `0.8540`
- **Threshold**: Scores $\ge 0.70$ are flagged as anomalous.

### `risk_score`
- **Data Type**: Float (Range `0.0` to `100.0`)
- **Business Meaning**: Composite risk rating synthesizing static threat vectors, ML anomaly scores, and failure status.
- **Example**: `85.0`
- **Formula**: $\min(\text{RulePoints} + \text{AnomalyPoints} + \text{StatusPenalty}, 100.0)$

### `severity`
- **Data Type**: String
- **Business Meaning**: Incident severity classification derived from composite risk score.
- **Valid Values**:
  - `CRITICAL` (Score $\ge 85.0$)
  - `HIGH` (Score $70.0 - 84.9$)
  - `MEDIUM` (Score $40.0 - 69.9$)
  - `LOW` (Score $20.0 - 39.9$)
  - `INFO` (Score $< 20.0$)

### `confidence`
- **Data Type**: Float (Range `0.50` to `0.99`)
- **Business Meaning**: Statistical confidence rating of the risk score based on the number of contributing threat factors.
- **Formula**: $\min(0.60 + 0.12 \times N_{\text{factors}}, 0.99)$

### `primary_reason`
- **Data Type**: String
- **Business Meaning**: Plain-language explanation of the leading risk factor triggering alert score.
- **Example**: `Geographical speed anomaly (1450 km/h across 8500 km)`

### `recommended_action`
- **Data Type**: String
- **Business Meaning**: Automated SOC playbook recommendation for Tier-1 analysts.
- **Example**: `CRITICAL: Immediately isolate endpoint, revoke user session tokens, enforce mandatory MFA reset, and initiate Playbook IR-104.`

---

## Table Relationships & Schema Mapping

```
+----------------+          +-------------------+          +-------------------+
|     users      |          |    auth_events    |          |    risk_alerts    |
+----------------+          +-------------------+          +-------------------+
| username (PK)  | <------- | event_id (PK)     | -------> | alert_id (PK)     |
| role           |          | username (FK)     |          | event_id (FK)     |
| first_seen     |          | ip_address        |          | risk_score        |
| last_seen      |          | risk_score        |          | primary_reason    |
+----------------+          +-------------------+          +-------------------+
```