# CyberGuard AI Platform - Product Requirements Document (PRD)

## 1. Executive Summary
**CyberGuard** is an enterprise-grade, AI-powered Cybersecurity Security Operations Center (SOC) Analytics platform. It ingests high-volume authentication attempt telemetry logs, identifies complex behavioral threat vectors (Brute Force, Credential Stuffing, Impossible Travel, Privilege Escalation), scores security events using an intelligent composite risk engine, benchmarks 5 Machine Learning anomaly detection algorithms, and presents actionable threat intelligence via an interactive dark-themed SOC dashboard with automated executive PDF reporting.

---

## 2. Target Personas & User Stories

### Persona 1: SOC Tier-1 Analyst (Alex)
- **Goal**: Quickly identify, filter, and respond to active critical security threats without manual log parsing.
- **User Story**: *"As a SOC Tier-1 Analyst, I want an interactive Incident Explorer with real-time risk scores and recommended SOC playbooks, so that I can immediately isolate compromised accounts and block hostile IPs."*
- **Acceptance Criteria**:
  - Filter authentication incidents by severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO`).
  - Search by IP address, username, or country.
  - View explicit contributing risk factors and step-by-step recommended remediation actions.

### Persona 2: Chief Information Security Officer / CISO (Elena)
- **Goal**: Monitor overall enterprise security posture, failure rates, and high-level threat trends for board-level briefings.
- **User Story**: *"As a CISO, I want high-level KPI cards, natural language AI briefings, and 1-click PDF executive report exports, so that I can brief board members on threat posture."*
- **Acceptance Criteria**:
  - Real-time KPI summary cards displaying Total Logins, Failure Rate %, High-Risk Alerts, and Critical Incidents.
  - 1-click PDF executive report generation via ReportLab and CSV incident data export.
  - Automated Natural Language AI narrative briefings summarizing key security events.

### Persona 3: Cyber Threat Intelligence & ML Engineer (Marcus)
- **Goal**: Benchmark anomaly detection algorithms and inspect behavioral outlier scores against historical baseline profiles.
- **User Story**: *"As an ML Threat Engineer, I want to compare Isolation Forest, One-Class SVM, Local Outlier Factor (LOF), DBSCAN, and Autoencoders side-by-side, so that I can validate production model performance."*
- **Acceptance Criteria**:
  - Benchmark evaluation matrix comparing Anomalies Detected, Precision, Recall, F1 Score, and Inference Latency.
  - Interactive scatter plots comparing Anomaly Scores vs Physical Travel Velocity (km/h).

---

## 3. Product Features & Capability Matrix

| Feature Module | Technical Specification | Business Value |
| :--- | :--- | :--- |
| **ETL & Data Engineering** | Schema validation, missing value handling, Haversine physical distance calculation, 10-min rolling failure and distinct user windowing | Clean, reliable telemetry ingestion pipeline |
| **Threat Indicator Engine** | Heuristic rules for Impossible Travel (>800 km/h), Brute Force (5+ fails/10m), Credential Stuffing (10+ users/10m), Privilege Escalation | Immediate deterministic threat vector tagging |
| **ML Anomaly Engine** | Isolation Forest production model with StandardScaler and MinMaxScaler normalized scores [0.0 - 1.0] | Zero-day behavioral anomaly discovery |
| **Multi-Model ML Benchmarker** | Side-by-side comparison of Isolation Forest, One-Class SVM, LOF, DBSCAN, and MLP Autoencoder | Algorithm validation & transparent model selection |
| **Composite Risk Engine** | Dynamic multi-factor scoring (0-100), severity mapping (`CRITICAL` to `INFO`), confidence ratings, and automated IR playbooks | Threat prioritization & SOC noise reduction |
| **AI Security Briefing** | Natural Language Security Briefings & Executive Threat Summaries | Rapid executive threat comprehension |
| **SQLite Analytical Database** | Relational schema (`users`, `devices`, `auth_events`, `risk_alerts`) with windowed analytical views (`v_user_risk_summary`, `v_threat_timeline`) | Deep forensic query capability & SIEM storage |
| **Enterprise SOC Dashboard** | Modular Streamlit dark glassmorphism UI with Plotly charts and 6 analytical views | Premium SOC analyst operational interface |
| **Automated Exporter** | ReportLab PDF layout generator with KPI metrics, threat distributions, incident tables, and playbooks | Compliance and executive reporting |

---

## 4. Key Performance Indicators (KPIs) & Success Metrics

- **Detection Precision & Recall**: > 90% detection rate on synthetic attack scenarios (Brute Force, Impossible Travel, Credential Stuffing).
- **False Positive Reduction**: Composite risk scoring weighting reduces raw anomaly alert volume by > 60%.
- **Inference Latency**: Sub-second execution (< 500 ms) for 1,500 authentication event pipeline processing.
- **System Stability & Quality**: 100% test pass rate across unit tests covering ETL, Threat Rules, ML Anomaly, Risk Engine, SQL DB, and Reporting.

---

## 5. Technology Stack & Dependencies

- **Programming Language**: Python 3.10+
- **Data Processing & Analytics**: Pandas, NumPy, Scikit-Learn
- **Web UI & Dashboard**: Streamlit, Plotly Express, Plotly Graph Objects
- **Database Engine**: SQLite3
- **PDF Generation**: ReportLab
- **Testing & Tooling**: Pytest
