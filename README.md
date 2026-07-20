# 🛡️ CyberGuard: Threat Intel & Behavioral Analytics Workspace

CyberGuard is a state-of-the-art cybersecurity analytics and threat intelligence workspace built for Security Operations Center (SOC) teams. It enables early detection of malicious authentication activities, provides granular user risk profiling, computes time-series security KPIs, and delivers actionable security insights. 

The system processes authentication logs, conducts temporal behavioral mapping, calculates user risk scores, runs advanced customer analytics and anomaly engines, stores telemetry in an SQLite database, and hosts a premium Streamlit dashboard.

---

## 🚀 Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/<YOUR-USERNAME>/SW2627-DataProduct-CyberGuard.git
cd SW2627-DataProduct-CyberGuard
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` before running the project:
```bash
cp .env.example .env
```
Inside `.env`, configure the SQLite database path:
```env
DATABASE_PATH=data/cyberguard.db
```

### 3. Create and Activate Virtual Environment
#### macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```
#### Windows (PowerShell):
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 📊 Streamlit SOC Threat Intel Dashboard

The workspace includes a high-performance **Streamlit Security Operations Center (SOC) Dashboard** that visualizes ingestion metrics, live threat logs, and behavioral profiles.

To run the dashboard locally:
```bash
streamlit run scripts/dashboard.py
```

### Dashboard Features:
* **Premium Dark Theme**: Custom glassmorphism UI styles tailored for security monitoring.
* **Global Telemetry Filters**: Filter logs in real-time by individual **Username** and/or login **Status** (Success vs. Failed).
* **Security KPI Cards**: Real-time counters showing *Total Login Attempts*, *Failed Attempts*, *Failure Rate*, and *High-Risk Alerts (Risk >= 70)*.
* **🚨 Alerts & Threat Log**: Live table of all authentication events, highlighting critical anomalies with risk scores ≥ 70.
* **👤 User Risk Profiles**: Aggregated table showing user profiles (computed by the pipeline) with calculated average and maximum risk scores.
* **📊 Analytics Panel**:
  - Failed logins categorized by origin Country (bar chart visualization).
  - Risk distribution categorized by severity: *Low (0-30)*, *Medium (31-69)*, and *High (70-100)*.

---

## 📂 Project Directory Structure

```
SW2627-DataProduct-CyberGuard/
│
├── data/
│   ├── raw/                           # Original raw datasets (unmodified)
│   │   ├── auth_logs.csv              # Authentication event log telemetry
│   │   ├── customers.csv              # Customer CRM records
│   │   ├── daily_revenue.csv          # Daily revenue tracking (raw)
│   │   ├── segment_data.csv           # Segmented customer dataset
│   │   └── ...                        # Cleaning/testing datasets (type_test.csv, data_with_dupes.csv)
│   ├── processed/                     # Cleaned, validated, and transformed outputs
│   │   ├── daily_revenue_processed.csv# Standardized daily revenue records
│   │   ├── segment_data_processed.csv # Cleaned user segmentation data
│   │   └── ...                        # Ingested and type-enforced tables
│   └── cyberguard.db                  # Central SQLite database storing auth logs and profiles
│
├── docs/
│   ├── DATA_DICTIONARY.md             # Data schemas, type constraints, and KPI definitions
│   └── data_dictionary.csv            # Structured schemas in CSV format
│
├── kpis/
│   ├── kpi_functions.py               # Analytical KPI computation formulas
│   ├── kpi_reference.md               # KPI mathematical formulas and owners
│   └── kpi_validation_targets.json    # Metric threshold targets for regressions
│
├── notebooks/                         # Exploratory and analytical Jupyter notebooks
│   ├── exploration.ipynb              # Baseline data exploration
│   ├── time_series_analysis.ipynb     # Chronological revenue and order trends
│   └── user_segmentation_analysis.ipynb# User clustering and behavioral segmentation
│
├── queries/                           # Canonical SQL metric files -- one truth for all teams
│   ├── monthly_active_users.sql       # MAU metric: distinct customers with FILTER segment breakdown
│   ├── revenue_by_segment.sql         # Monthly revenue + order metrics joined by customer type
│   └── conversion_funnel.sql          # Daily signup → email verify → first purchase funnel
│
├── scripts/                           # Production scripts and pipeline orchestrators
│   ├── anomaly_detection.py           # Z-score-based daily telemetry anomaly finder
│   ├── correlation_analysis.py        # Heatmap correlation builder and feature selector
│   ├── dashboard.py                   # Streamlit SOC threat intelligence application
│   ├── data_workflow.py               # Core modular ingest-process-output data workflow
│   ├── datetime_feature_engineering.py# Temporal log parser and recency extractor
│   ├── deduplicate_data.py            # Deduplication auditor and cleaner
│   ├── enforce_types.py               # Data type compliance validation engine
│   ├── funnel_analysis.py             # Acquisition and purchase funnel visualizer
│   ├── generate_mock_data.py          # Synthetic dataset generator for development
│   ├── handle_missing.py              # Null value imputation engine
│   ├── ingest_data.py                 # Flattening and loading formats (CSV/JSON/Nested)
│   ├── pipeline.py                    # Main data validation pipeline script
│   ├── profile_data.py                # Dataset quality profiler and column masker
│   ├── revenue_distribution_analysis.py# Revenue concentration and Gini curve plotter
│   ├── rolling_metrics.py             # Resampler and rolling-average calculator
│   ├── root_cause_investigation.py    # Threat incident root-cause analyzer
│   ├── segment_analysis.py            # Customer cohort aggregator and heatmap builder
│   ├── segment_groupby_analysis.py    # Reshaping and reshaping of segmentation tables
│   ├── sql_business_metrics.py        # SQL Business Metrics runner (Assignment 2.38)
│   ├── string_cleaning_pipeline.py    # Whitespace trim and text cleaning pipeline
│   └── validate_intake.py             # Schema structural integrity validator
│
├── output/                            # Saved charts, JSON audits, and markdown reports
└── requirements.txt                   # Complete library dependency manifest
```

---

## ⚙️ Core Engineering Modules

### 1. Ingestion & Quality Cleaning
* **`scripts/ingest_data.py` & `scripts/validate_intake.py`**:
  Flattens and parses raw CRM datasets (CSV/JSON/Nested JSON) into standardized pandas DataFrames, validating schema structures prior to processing.
* **`scripts/deduplicate_data.py` & `scripts/enforce_types.py`**:
  Identifies exact duplicate records and casts mismatched data types (e.g., numbers, datetimes, booleans) to prevent type coercion errors down the line. Generates `output/dedup_summary.json` and `output/type_enforcement_report.json`.
* **`scripts/handle_missing.py`**:
  Imputes null entries using column-wise median values (for numbers) or drop-rules, logging actions in `output/imputation_decisions.json`.
* **`scripts/string_cleaning_pipeline.py`**:
  Cleans dirty text fields by removing special characters, stripping trailing spaces, and normalizing string cases.
* **`scripts/profile_data.py`**:
  Generates a full report (`output/profile_report.json`) detailing null percentages, unique frequencies, and statistics. It automatically hashes sensitive identifiers (like emails) to comply with data privacy regulations.

### 2. Feature & Temporal Engineering
* **`scripts/datetime_feature_engineering.py`**:
  Normalizes datetime fields to an explicit format and derives temporal features: `hour`, `day_of_week`, `is_business_hour`, and time-of-day categories (Morning, Afternoon, Evening, Night). It also calculates customer recency (days elapsed since last transaction).

### 3. Key Performance Indicators (KPI) Engine
The KPI engine in [kpi_functions.py](file:///w:/Kalvium/5th%20Sem/SW2627-DataProduct-CyberGuard/kpis/kpi_functions.py) calculates crucial operational and financial metrics:
* **Monthly Active Users (MAU)**: Unique customers who performed transactions or logins in the last 30 days. Target: `5,000 - 6,000`.
* **Revenue per Customer**: Average revenue generated per customer. Target: `$90 - $110`.
* **Churn Rate**: Cohort-based customer loss rates. Target: `0% - 5%`.
* **Payment Success Rate**: Successful payments divided by total attempts. Target: `95% - 100%`.
* **Customer Acquisition Cost (CAC)**: Spend required to acquire a new customer. Target: `$0 - $50`.
* **Repeat Purchase Rate**: Percentage of customers making >1 purchase. Target: `25% - 45%`.

Validation checks are configured in `kpis/kpi_validation_targets.json`. More details are in [kpi_reference.md](file:///w:/Kalvium/5th%20Sem/SW2627-DataProduct-CyberGuard/kpis/kpi_reference.md).

---

## 🔬 Advanced Analytics & Visualizations

### 1. Segmentation Analysis
* **`scripts/segment_analysis.py` & `scripts/segment_groupby_analysis.py`**:
  Aggregates users into **Enterprise**, **SMB**, and **Startup** segments. It creates a ranked performance dashboard saved to `output/segment_analysis_report.txt` and a normalized performance index heatmap saved to `output/segment_heatmap.png` (using green for good and red for bad performance indicator scales).
  
  *Key Cohort Insights:*
  - **Enterprise**: High average LTV (~$146k), near-perfect retention (~720 days), and low churn (~0.0%).
  - **SMB**: High support ticket volume (average ~2.5) and severe churn issues (~12.0%).
  - **Startup**: High quantity (55% of user base) but lowest economic yield (average LTV ~$2k).

### 2. Time-Series Trends & Rolling Statistics
* **`scripts/rolling_metrics.py`**:
  Orchestrates resampling of daily metrics into weekly/monthly buckets, computes 7-day and 30-day moving averages (saved as `output/rolling_avg.png`), and tracks cumulative revenue.
* **`scripts/revenue_distribution_analysis.py` & `scripts/funnel_analysis.py`**:
  Plot transaction distributions (skewness, cumulative curves) and trace stage-by-stage marketing funnel conversions (Impressions to Purchases, outputting `output/funnel_chart.png`).
* **`scripts/correlation_analysis.py`**:
  Runs Pearson and Spearman tests between metrics (engagement, tickets, tenure, churn) and flags strong pairs in `output/strong_correlation_pairs.csv` and a heatmap `output/correlation_heatmap.png`.

---

## 🛡️ Security Anomaly & Incident Investigation Engines

### 1. Anomaly Detection
* **`scripts/anomaly_detection.py`**:
  Employs a z-score thresholding approach (outlier identification) on daily revenue and transaction logs. It creates an audit log of outliers saved to `output/anomalies_log.csv` and draws a trend line anomaly highlight chart in `output/anomaly_detection.png`.

### 2. Incident Root-Cause Investigation
* **`scripts/root_cause_investigation.py`**:
  Diagnoses localized authentication drops on the security servers by scanning affected times, identifying surrounding success rates, and running cross-tab analyses across usernames, devices, and countries.
  
  *Case Study: 2026-07-05 Security Incident*
  - **Anomaly Detected**: Daily login success rate plummeted to **69.6%** (normally above 80.4%).
  - **Epicenter Isolated**: A 0% login success rate occurred during the **15:00 - 16:00 UTC** hour.
  - **Key Correlated Dimensions**: The drop was entirely localized to user **`user_9`**, originating from country **`IN`**, utilizing a **`Laptop-macOS`** device. This isolated breach/issue was mapped in detail in `output/investigation_report.txt` and `output/investigation_summary.json`.

---

## 📐 SQL Business Metrics (Assignment 2.38)

The `queries/` directory stores **canonical SQL metric definitions** — written once, reused by every team.  
No more five people computing "Monthly Revenue" five different ways.

| File | Purpose |
|------|---------|
| `queries/monthly_active_users.sql` | Distinct customers per month + Enterprise/SMB/Startup breakdown via `FILTER` |
| `queries/revenue_by_segment.sql`   | Monthly revenue, order count, avg order value, revenue-per-customer by segment |
| `queries/conversion_funnel.sql`    | Daily signup → email verify → first purchase funnel with `conversion_pct` |

**Runner & Validator**: `scripts/sql_business_metrics.py` seeds synthetic business-metric tables (`transactions`, `customers`, `users`), executes the queries via `pd.read_sql()`, and runs a full validation suite checking for nulls, value ranges, segment coverage, and funnel consistency.

```bash
python scripts/sql_business_metrics.py
```

---

## 🛠️ Execution Guide (CLI Checklist)

Run these commands from the project root directory to execute the analytical modules:

```bash
# 1. Run the core ingestion and data cleaning workflow pipeline
python scripts/data_workflow.py

# 2. Run the main processing and type validation pipeline
python scripts/pipeline.py

# 3. Profile dataset quality (generates JSON quality metrics and redactions)
python scripts/profile_data.py --input data/raw/quality_test.csv --output output/profile_report.json

# 4. Extract temporal and datetime features
python scripts/datetime_feature_engineering.py

# 5. Compute time-series rolling averages and trends
python scripts/rolling_metrics.py

# 6. Execute cohort segmentation analysis and produce segment heatmaps
python scripts/segment_analysis.py

# 7. Run statistical correlation analysis and generate heatmaps
python scripts/correlation_analysis.py

# 8. Conduct Gini distribution analysis on revenue data
python scripts/revenue_distribution_analysis.py

# 9. Perform stage-by-stage acquisition funnel analysis
python scripts/funnel_analysis.py

# 10. Run daily telemetry anomaly detection
python scripts/anomaly_detection.py

# 11. Run root-cause diagnostics on auth logs
python scripts/root_cause_investigation.py

# 12. Run SQL business metrics (Assignment 2.38)
python scripts/sql_business_metrics.py

# 13. Run the interactive Streamlit SOC dashboard
streamlit run scripts/dashboard.py
```

---

## 📖 Data Dictionary

For comprehensive schema details, data type constraints, null-handling specifications, and business rules mapped to each CRM column and authentication parameter, please refer to [DATA_DICTIONARY.md](file:///w:/Kalvium/5th%20Sem/SW2627-DataProduct-CyberGuard/docs/DATA_DICTIONARY.md).

