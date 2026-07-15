# Data Dictionary

## Dataset Overview
This dataset contains customer transaction records updated daily from the CRM system and authentication logs updated in real-time from our security server.
Last Updated: 2026-07-14
Maintained By: Data Engineering Team

## Columns

### customer_id
- **Type**: Integer
- **Business Meaning**: Unique customer identifier from CRM system
- **Example**: 12456
- **Null Handling**: Never null (primary key)
- **Related KPI**: Customer tracking, lifetime value calculation
- **Updates**: Assigned when customer created in CRM

### trnx_amt
- **Type**: Float
- **Business Meaning**: Revenue from single transaction
- **Example**: 150.99
- **Unit**: USD
- **Null Handling**: Very rare - investigate if found
- **Related KPI**: Monthly revenue, average transaction value, customer lifetime value
- **Updates**: Set when transaction completes

### purchase_date
- **Type**: Datetime
- **Business Meaning**: Timestamp when the sale was completed
- **Example**: 2025-01-15
- **Unit**: UTC
- **Null Handling**: Never null for completed transactions
- **Related KPI**: Sales velocity, revenue trends, cohort analysis
- **Updates**: Recorded at transaction close

### cust_segment
- **Type**: String
- **Business Meaning**: Customer market segment (B2B/B2C/SMB)
- **Valid Values**: B2B, B2C, SMB
- **Example**: B2B
- **Null Handling**: If null, classify as UNKNOWN
- **Related KPI**: Segment revenue, segment churn rate
- **Updates**: Monthly from CRM classification

### flag_churn
- **Type**: Integer
- **Business Meaning**: Binary churn indicator for retention modeling
- **Example**: 0
- **Valid Values**: 0 or 1
- **Null Handling**: Never null for labeled training sets
- **Related KPI**: Churn rate, retention performance
- **Updates**: Derived after the churn observation window closes

### segment
- **Type**: String
- **Business Meaning**: Ambiguous segment label that should be interpreted as customer market segment
- **Example**: SMB
- **Null Handling**: Investigate if missing because it affects grouping logic
- **Related KPI**: Segment revenue, segment profitability
- **Updates**: Prefer renaming to market_segment in future schema revisions

### customer_name
- **Type**: String
- **Business Meaning**: Human-readable customer reference display name
- **Example**: Alice Smith
- **Null Handling**: Standardize formatting, default to "Unknown Customer" if missing
- **Related KPI**: Customer segmentation analysis
- **Updates**: Synchronized nightly from the CRM database

### email
- **Type**: String
- **Business Meaning**: Customer contact email address
- **Example**: alice@example.com
- **Null Handling**: Deduplicate and enforce syntax validation
- **Related KPI**: Customer communication
- **Updates**: Collected at registration

### timestamp
- **Type**: Datetime
- **Business Meaning**: Precise timestamp of when the login attempt occurred
- **Example**: 2026-07-01 13:39:45
- **Unit**: UTC
- **Null Handling**: Never null for any authentication event
- **Related KPI**: Login velocity, brute-force window tracking
- **Updates**: Recorded automatically at time of connection request

### username
- **Type**: String
- **Business Meaning**: Account identifier (username) associated with the login attempt
- **Example**: user_16
- **Null Handling**: If missing, catalog as "anonymous" and investigate as potential threat
- **Related KPI**: User risk profiling, account credential tracking
- **Updates**: Input by client in login form

### ip_address
- **Type**: String
- **Business Meaning**: The originating IPv4 address of the connection
- **Example**: 21.73.167.18
- **Null Handling**: Never null
- **Related KPI**: Brute force source count, anomalous IP tracking
- **Updates**: Captured from network socket

### country
- **Type**: String
- **Business Meaning**: Geolocation country code (ISO two-letter) derived from login IP address
- **Example**: IN
- **Null Handling**: Default to "XX" if geoinfo cannot be determined
- **Related KPI**: Geographic risk, impossible travel anomaly
- **Updates**: Resolved via IP geolocation lookup database

### status
- **Type**: String
- **Business Meaning**: Outcome of the login attempt
- **Valid Values**: Success, Failed
- **Example**: Failed
- **Null Handling**: Fail-closed (treated as failed if undefined)
- **Related KPI**: Failed login rate, brute force detection
- **Updates**: Returned by authentication server backend

### device_type
- **Type**: String
- **Business Meaning**: Identifier of the device and OS combination making the login request
- **Example**: Mobile-iOS
- **Null Handling**: Default to "Unknown-OS"
- **Related KPI**: Device profiling anomalies
- **Updates**: Extracted from browser User-Agent header

### risk_score
- **Type**: Float
- **Business Meaning**: Calculated security risk score (range 0 to 100) assigned by CyberGuard analysis
- **Example**: 75.0
- **Null Handling**: Defaults to 10.0 (baseline risk)
- **Related KPI**: High-risk event rate, threat profile count
- **Updates**: Computed during pipeline behavioral analysis

## Column to KPI Mapping

### Monthly Revenue
- **Formula**: SUM(trnx_amt)
- **Related Columns**: trnx_amt, purchase_date
- **Why It Matters**: Tracks total company revenue
- **Update Frequency**: Daily

### Sales Velocity
- **Formula**: COUNT(transactions) / days
- **Related Columns**: purchase_date
- **Why It Matters**: Measures sales activity rate and momentum
- **Update Frequency**: Weekly

### Segment Revenue
- **Formula**: SUM(trnx_amt) grouped by cust_segment
- **Related Columns**: trnx_amt, cust_segment
- **Why It Matters**: Identifies most profitable market segments
- **Update Frequency**: Monthly

### Churn Rate
- **Formula**: SUM(flag_churn) / total_customers
- **Related Columns**: flag_churn, customer_id
- **Why It Matters**: Critical retention metric
- **Update Frequency**: Quarterly

### Customer Lifetime Value
- **Formula**: SUM(trnx_amt) grouped by customer_id over time
- **Related Columns**: customer_id, trnx_amt, purchase_date
- **Why It Matters**: Highlights high-value customers for retention and upsell planning
- **Update Frequency**: Monthly

### Failed Login Rate
- **Formula**: COUNT(status == 'Failed') / COUNT(status) grouped by username
- **Related Columns**: status, username, timestamp
- **Why It Matters**: Identifies targeted users undergoing active brute force or credential stuffing attacks
- **Update Frequency**: Daily

### Geographic Risk Score
- **Formula**: AVG(risk_score) grouped by country
- **Related Columns**: risk_score, country
- **Why It Matters**: Visualizes geolocation hotspots for cybersecurity threats
- **Update Frequency**: Hourly

## Ambiguous Columns & Resolutions

### Column: flag_churn
- **Original Ambiguity**: Does it mean "currently churned" or "will churn in future"?
- **Resolved Meaning**: Binary indicator of whether customer churned in 90 days following this transaction
- **Business Interpretation**: Historical churn flag used for training predictive retention models
- **Proposed Rename**: has_churned_90d
- **Risk If Misunderstood**: Models trained on wrong definition produce unreliable predictions

### Column: segment
- **Original Ambiguity**: Is this market segment, customer segment, product segment, or geographic region?
- **Resolved Meaning**: Customer market segment (B2B, B2C, SMB) - determines go-to-market strategy
- **Business Interpretation**: Informs pricing strategy and sales approach
- **Proposed Rename**: market_segment
- **Risk If Misunderstood**: Revenue analysis by wrong dimension produces misleading segment performance

### Column: status
- **Original Ambiguity**: Is this a transaction processing status (e.g. pending/settled) or login authentication status?
- **Resolved Meaning**: Authentication attempt outcome (Success or Failed)
- **Business Interpretation**: Tells security operations center (SOC) whether a credential entry succeeded or failed
- **Proposed Rename**: login_outcome
- **Risk If Misunderstood**: Grouping transaction status and login status leads to completely wrong metrics

## Column Relationships

### Revenue per Customer
- **Definition**: SUM(trnx_amt) grouped by customer_id
- **How It Matters**: Identifies high-value customers for retention focus and upsell opportunities
- **Example**: "Top 10% of customers generate 50% of revenue"
- **Related Columns**: customer_id, trnx_amt, cust_segment

### Churn by Segment
- **Definition**: SUM(flag_churn) / SUM(all customers) grouped by cust_segment
- **How It Matters**: Identifies which segments have highest churn risk requiring intervention
- **Example**: "SMB segment has 25% churn vs 10% for B2B"
- **Related Columns**: flag_churn, cust_segment, customer_id

### Revenue Velocity
- **Definition**: Rolling sum of trnx_amt over 30-day windows
- **How It Matters**: Tracks sales momentum and growth rate trends
- **Example**: "Monthly revenue velocity trending up 15% quarter-over-quarter"
- **Related Columns**: trnx_amt, purchase_date

### Impossible Travel Anomaly
- **Definition**: Multiple login events from the same username in different country values within a time window where travel is physically impossible
- **How It Matters**: High-confidence indicator of account sharing or credential compromise
- **Example**: "User logs in from JP at 14:04, then from IN at 15:04"
- **Related Columns**: username, country, timestamp, risk_score

### IP Brute Force Threshold
- **Definition**: COUNT(status == 'Failed') > 5 grouped by ip_address
- **How It Matters**: Flagging host IP addresses that are actively launching automated login attacks
- **Example**: "IP 1.2.3.4 attempts 10 logins, all failing; automatically increases risk score by 25 points"
- **Related Columns**: ip_address, status, risk_score