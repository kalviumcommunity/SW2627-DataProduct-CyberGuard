# CyberGuard AI Platform - Low-Level Design (LLD)

## 1. Codebase Directory Blueprint

```
SW2627-DataProduct-CyberGuard/
├── app.py                          # Streamlit Entry Point & Navigation Controller
├── PRD.md                          # Product Requirements Document
├── HLD.md                          # High-Level Architecture Design
├── LLD.md                          # Low-Level Component Design
├── DESIGN_SYSTEM.md                # UI Design Token Guidelines
├── README.md                       # Project Setup & Documentation Guide
├── cyberguard/                     # Core Python Package
│   ├── __init__.py
│   ├── config/                     # System Settings & Thresholds
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── utils/                      # Utilities & Logging
│   │   ├── __init__.py
│   │   └── logger.py
│   ├── etl/                        # Ingestion, Feature Engineering & Validation
│   │   ├── __init__.py
│   │   ├── generator.py
│   │   ├── validator.py
│   │   └── pipeline.py
│   ├── analytics/                  # Rule Detection & Profiling
│   │   ├── __init__.py
│   │   ├── threat_rules.py
│   │   └── profiler.py
│   ├── models/                     # Production ML & Multi-Model Benchmarker
│   │   ├── __init__.py
│   │   ├── anomaly_engine.py
│   │   └── benchmarker.py
│   ├── risk/                       # Composite Risk Engine
│   │   ├── __init__.py
│   │   └── risk_engine.py
│   ├── ai/                         # Natural Language Intelligence Engine
│   │   ├── __init__.py
│   │   └── insight_engine.py
│   ├── sql/                        # SQLite Schema, Ingestion & Views
│   │   ├── __init__.py
│   │   ├── db_manager.py
│   │   └── queries.py
│   ├── reporting/                  # ReportLab PDF & CSV Exporter
│   │   ├── __init__.py
│   │   └── report_generator.py
│   └── dashboard/                  # Streamlit Views & Custom CSS Components
│       ├── __init__.py
│       ├── components.py
│       ├── views_overview.py
│       ├── views_incidents.py
│       ├── views_anomalies.py
│       ├── views_geo.py
│       ├── views_profiles.py
│       └── views_sql.py
├── data/                           # Data Directories (raw / processed)
├── logs/                           # System Operation Logs
└── tests/                          # Pytest Unit Test Suite
    ├── test_etl.py
    ├── test_models.py
    ├── test_reporting.py
    ├── test_risk_engine.py
    ├── test_sql.py
    └── test_threat_rules.py
```

---

## 2. Config & Settings Specification (`cyberguard/config/settings.py`)

Centralized configuration constants:

```python
# Directory Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
OUTPUT_DIR = BASE_DIR / "output"
REPORTS_DIR = BASE_DIR / "reports"
DATABASE_PATH = OUTPUT_DIR / "cyberguard_soc.db"

# Cybersecurity Threshold Constants
IMPOSSIBLE_TRAVEL_SPEED_KMH = 800.0       # Physical velocity cutoff (km/h)
BRUTE_FORCE_FAIL_THRESHOLD = 5             # Failed login attempts in 10-min window
CREDENTIAL_STUFFING_USER_COUNT = 10        # Distinct usernames attempted per IP in 10 min
PRIVILEGE_ESCALATION_TARGETS = ["root", "admin", "sysadmin"]

# Machine Learning Engine Hyperparameters
ML_CONTAMINATION_RATE = 0.05                # Expected outlier ratio (5%)
ML_MODEL_RANDOM_STATE = 42
```

---

## 3. Data Telemetry & ETL Pipeline Specification (`cyberguard/etl/`)

### 3.1 Haversine Distance Formula (`pipeline.py`)

Calculates the Great Circle physical distance between consecutive login coordinates:

$$\text{dlat} = \text{radians}(\text{lat}_2 - \text{lat}_1), \quad \text{dlon} = \text{radians}(\text{lon}_2 - \text{lon}_1)$$
$$a = \sin^2\left(\frac{\text{dlat}}{2}\right) + \cos(\text{radians}(\text{lat}_1)) \cdot \cos(\text{radians}(\text{lat}_2)) \cdot \sin^2\left(\frac{\text{dlon}}{2}\right)$$
$$c = 2 \cdot \arcsin(\sqrt{a}), \quad d = R \cdot c \quad (R = 6371.0\text{ km})$$

```python
def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float
```

### 3.2 Data Validator (`validator.py`)

```python
class DataValidator:
    REQUIRED_COLUMNS: List[str] = [
        "timestamp", "username", "ip_address", "country", "city",
        "latitude", "longitude", "status", "device_type", "user_agent"
    ]

    @staticmethod
    def validate_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Verify presence of mandatory telemetry schema columns."""

    @staticmethod
    def clean_and_validate(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Convert timestamps, impute missing values, and normalize IP syntax."""
```

### 3.3 ETL Pipeline Orchestrator (`pipeline.py`)

```python
class ETLPipeline:
    def __init__(self, raw_csv_path: Path = None):
        self.raw_csv_path = raw_csv_path or (RAW_DATA_DIR / "auth_logs.csv")

    def load_raw_data(self) -> pd.DataFrame: ...
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame: ...
    def run(self) -> Tuple[pd.DataFrame, Dict[str, Any]]: ...
```

**Engineered Feature Columns**:
- `is_failed` (1 if status == 'Failed' else 0)
- `is_success` (1 if status == 'Success' else 0)
- `hour`, `day_of_week`, `is_weekend`
- `prev_timestamp`, `prev_lat`, `prev_lon`, `prev_country`
- `time_diff_min`: Elapsed minutes since user's previous attempt.
- `geo_dist_km`: Haversine distance in km.
- `geo_speed_kmh`: Physical travel speed ($\text{dist} / \text{hours}$).
- `ip_failed_count_10m`: Rolling 10-minute failed logins from originating IP.
- `user_failed_count_10m`: Rolling 10-minute failed logins for target user.
- `ip_distinct_users_10m`: Rolling 10-minute count of unique usernames attempted by originating IP.

---

## 4. Analytics & Threat Heuristics Specification (`cyberguard/analytics/threat_rules.py`)

```python
class ThreatRuleEngine:
    @staticmethod
    def detect_impossible_travel(row: pd.Series) -> bool:
        # Returns True if geo_speed_kmh > 800.0 AND geo_dist_km > 100.0

    @staticmethod
    def detect_brute_force(row: pd.Series) -> bool:
        # Returns True if user_failed_count_10m >= 5 OR ip_failed_count_10m >= 5

    @staticmethod
    def detect_credential_stuffing(row: pd.Series) -> bool:
        # Returns True if ip_distinct_users_10m >= 10

    @staticmethod
    def detect_privilege_escalation(row: pd.Series) -> bool:
        # Returns True if username in ['root', 'admin', 'sysadmin'] AND status == 'Failed'

    def evaluate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        # Attaches flag_impossible_travel, flag_brute_force, flag_credential_stuffing,
        # flag_privilege_escalation, and threat_vector string.
```

---

## 5. Machine Learning Engines (`cyberguard/models/`)

### 5.1 Production Anomaly Engine (`anomaly_engine.py`)

```python
FEATURE_COLUMNS = [
    "is_failed", "hour", "day_of_week", "is_weekend",
    "time_diff_min", "geo_dist_km", "geo_speed_kmh",
    "ip_failed_count_10m", "user_failed_count_10m", "ip_distinct_users_10m"
]

class AnomalyEngine:
    def __init__(self, contamination: float = ML_CONTAMINATION_RATE):
        self.contamination = contamination
        self.scaler = StandardScaler()
        self.score_scaler = MinMaxScaler(feature_range=(0.0, 1.0))
        self.model = IsolationForest(
            n_estimators=100,
            contamination=self.contamination,
            random_state=42,
            n_jobs=-1
        )

    def fit_predict(self, df: pd.DataFrame) -> pd.DataFrame:
        # 1. Fits StandardScaler on FEATURE_COLUMNS
        # 2. Inverts raw decision function scores (-raw_scores)
        # 3. Scales scores to [0.0, 1.0] using MinMaxScaler
        # 4. Attaches anomaly_score, is_anomaly (score >= 0.70), anomaly_confidence
```

### 5.2 Multi-Model ML Benchmarker (`benchmarker.py`)

```python
class ModelBenchmarker:
    def __init__(self, contamination: float = ML_CONTAMINATION_RATE): ...
    def prepare_features(self, df: pd.DataFrame) -> np.ndarray: ...
    def benchmark_models(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]: ...
```

**Evaluated Algorithms**:
1. **Isolation Forest**: Tree isolation partitioning.
2. **One-Class SVM**: Hyperplane separation with RBF kernel.
3. **Local Outlier Factor (LOF)**: $k$-nearest neighbor local density score ($k=20$).
4. **DBSCAN**: Density-based spatial clustering ($\text{eps}=2.5, \text{min\_samples}=5$).
5. **MLP Autoencoder**: Neural reconstruction error ($8 \to 4 \to 8$ hidden architecture, MSE error thresholding).

---

## 6. Composite Risk Engine Specification (`cyberguard/risk/risk_engine.py`)

### 6.1 Score Calculation Formula

$$\text{RiskScore} = \min\left( \text{BaseScore}_{\text{Rules}} + \text{Score}_{\text{ML}} + \text{Penalty}_{\text{Status}}, \ 100.0 \right)$$

- **Brute Force Flag**: $+45.0$
- **Impossible Travel Flag**: $+40.0$
- **Credential Stuffing Flag**: $+50.0$
- **Privilege Escalation Flag**: $+35.0$
- **ML Anomaly Score ($>0.5$)**: $+(\text{anomaly\_score} \times 30.0)$
- **Failed Status**: $+10.0$

### 6.2 Severity & Confidence Classification Table

| Risk Score Range | Severity Tag | Confidence Formula | Recommended Playbook |
| :--- | :--- | :--- | :--- |
| **85.0 - 100.0** | `CRITICAL` | $\min(0.60 + 0.12 \times N_{\text{factors}}, 0.99)$ | Revoke session tokens, force MFA reset, execute IR-104 playbook. |
| **70.0 - 84.9** | `HIGH` | $\min(0.60 + 0.12 \times N_{\text{factors}}, 0.99)$ | Block IP on perimeter firewall, lock user account 60 minutes. |
| **40.0 - 69.9** | `MEDIUM` | $\min(0.60 + 0.12 \times N_{\text{factors}}, 0.99)$ | Enforce step-up MFA, monitor account for 24 hours. |
| **20.0 - 39.9** | `LOW` | $\min(0.60 + 0.12 \times N_{\text{factors}}, 0.99)$ | Log event to SIEM, update user baseline profile. |
| **0.0 - 19.9** | `INFO` | $0.60$ | Baseline normal authentication; no action required. |

---

## 7. SQLite Relational Schema Specification (`cyberguard/sql/db_manager.py`)

### 7.1 DDL Schema Definitions

```sql
-- 1. Users Normalized Master Table
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    role TEXT DEFAULT 'Standard'
);

-- 2. Devices Table
CREATE TABLE IF NOT EXISTS devices (
    device_id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_type TEXT UNIQUE
);

-- 3. Auth Events Fact Table
CREATE TABLE IF NOT EXISTS auth_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP NOT NULL,
    username TEXT NOT NULL,
    ip_address TEXT NOT NULL,
    country TEXT,
    city TEXT,
    latitude REAL,
    longitude REAL,
    status TEXT NOT NULL,
    device_type TEXT,
    user_agent TEXT,
    threat_vector TEXT,
    anomaly_score REAL,
    risk_score REAL,
    severity TEXT,
    confidence REAL,
    primary_reason TEXT,
    recommended_action TEXT,
    FOREIGN KEY (username) REFERENCES users (username)
);

-- 4. Risk Alerts Summary Queue
CREATE TABLE IF NOT EXISTS risk_alerts (
    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,
    timestamp TIMESTAMP,
    username TEXT,
    severity TEXT,
    risk_score REAL,
    primary_reason TEXT,
    FOREIGN KEY (event_id) REFERENCES auth_events (event_id)
);

-- Indexes for SOC Analytical Query Performance
CREATE INDEX IF NOT EXISTS idx_auth_username_ts ON auth_events (username, timestamp);
CREATE INDEX IF NOT EXISTS idx_auth_ip ON auth_events (ip_address);
CREATE INDEX IF NOT EXISTS idx_auth_risk ON auth_events (risk_score);
CREATE INDEX IF NOT EXISTS idx_auth_severity ON auth_events (severity);

-- Analytical View 1: User Risk Aggregation
CREATE VIEW IF NOT EXISTS v_user_risk_summary AS
SELECT 
    username,
    COUNT(*) as total_logins,
    SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) as total_failures,
    ROUND(CAST(SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) AS REAL) / COUNT(*) * 100.0, 2) as failure_rate_pct,
    MAX(risk_score) as max_risk_score,
    AVG(risk_score) as avg_risk_score,
    COUNT(DISTINCT ip_address) as distinct_ips,
    COUNT(DISTINCT country) as distinct_countries
FROM auth_events
GROUP BY username;

-- Analytical View 2: High Severity Timeline
CREATE VIEW IF NOT EXISTS v_threat_timeline AS
SELECT 
    event_id, timestamp, username, ip_address, country,
    status, threat_vector, risk_score, severity, primary_reason
FROM auth_events
WHERE risk_score >= 70.0
ORDER BY timestamp DESC;
```

---

## 8. Reporting & AI Intelligence Specifications

### 8.1 Natural Language AI Security Engine (`cyberguard/ai/insight_engine.py`)

```python
class SecurityInsightEngine:
    @staticmethod
    def generate_executive_briefing(df: pd.DataFrame) -> str:
        """Synthesize dataset statistics into markdown CISO briefing narrative."""

    @staticmethod
    def explain_incident(row: pd.Series) -> str:
        """Generate plain-text forensic explanation of specific event risk factors."""
```

### 8.2 PDF & CSV Exporter (`cyberguard/reporting/report_generator.py`)

```python
class SOCReportGenerator:
    def __init__(self, output_dir: Path = REPORTS_DIR): ...
    def generate_pdf_report(self, df: pd.DataFrame, output_path: Path = None) -> Path:
        # Generates multi-page ReportLab PDF with executive metrics, charts, alert tables, and playbooks.
    def generate_csv_export(self, df: pd.DataFrame, output_path: Path = None) -> Path:
        # Exports high-risk incidents to CSV file.
```

---

## 9. Streamlit Dashboard Architecture (`app.py` & `cyberguard/dashboard/`)

`app.py` sets up page config, runs the `@st.cache_data` pipeline loader `load_and_process_pipeline_data()`, applies the dark SOC glassmorphism design system via `apply_soc_theme()`, renders the sidebar, and routes navigation to 6 views:

1. **SOC Executive Overview** (`views_overview.py`): Top KPI metric tiles, risk distribution donut chart, threat vector breakdown bar chart, and AI Executive Briefing panel.
2. **Real-Time Incident Explorer** (`views_incidents.py`): Multi-select filters (Severity, Status, Threat Vector, Search box), incident table with color badges, detailed threat factor inspection modal, and 1-click PDF/CSV report download buttons.
3. **ML Anomaly & Benchmark** (`views_anomalies.py`): Production Isolation Forest anomaly distribution, scatter plot (Anomaly Score vs Speed), and 5-Model Benchmark matrix comparison.
4. **Geo & Impossible Travel** (`views_geo.py`): World Scatter Geo map of authentications colored by risk score, travel velocity distribution histogram, and impossible travel incident table.
5. **User & Device Profiler** (`views_profiles.py`): Individual user activity breakdown, failure rate history, device breakdown, and risk profile summary.
6. **SQL Analytical Studio** (`views_sql.py`): Interactive SQL query execution box against SQLite database with pre-built query buttons (`User Risk Summary View`, `High Risk Timeline View`, `Top Failure IPs`).

---

## 10. Verification & Test Coverage Matrix

The codebase maintains 100% test pass rate across 6 test modules:

| Test File | Target Component | Verification Scope |
| :--- | :--- | :--- |
| `test_etl.py` | `ETLPipeline`, `DataValidator` | Synthetic log generation, schema validation, missing data cleaning, feature calculations. |
| `test_threat_rules.py` | `ThreatRuleEngine` | Heuristic evaluation for Impossible Travel, Brute Force, Credential Stuffing, Privilege Escalation. |
| `test_models.py` | `AnomalyEngine`, `ModelBenchmarker` | Isolation Forest anomaly scoring range [0.0, 1.0], 5-model benchmark metrics generation. |
| `test_risk_engine.py` | `RiskEngine` | Composite score calculation, score capping at 100.0, severity level assignment, playbook mapping. |
| `test_sql.py` | `DatabaseManager` | Schema initialization, table ingestion, view querying (`v_user_risk_summary`, `v_threat_timeline`). |
| `test_reporting.py` | `SOCReportGenerator` | PDF and CSV report creation in filesystem. |
