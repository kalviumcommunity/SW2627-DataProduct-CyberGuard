"""
CyberGuard AI Cybersecurity Analytics Platform - Main Streamlit Application
"""
import streamlit as st
import pandas as pd
from pathlib import Path

# Page Config
st.set_page_config(
    page_title="CyberGuard SOC Threat Intel & Analytics",
    page_icon="https://img.icons8.com/nolan/96/shield.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

from cyberguard.config.settings import PROCESSED_DATA_DIR, DATABASE_PATH
from cyberguard.etl.pipeline import ETLPipeline
from cyberguard.analytics.threat_rules import ThreatRuleEngine
from cyberguard.models.anomaly_engine import AnomalyEngine
from cyberguard.risk.risk_engine import RiskEngine
from cyberguard.sql.db_manager import DatabaseManager

from cyberguard.dashboard.components import apply_soc_theme, render_header, APP_LOGO_SVG, get_svg_icon
from cyberguard.dashboard.views_overview import render_overview_view
from cyberguard.dashboard.views_incidents import render_incidents_view
from cyberguard.dashboard.views_anomalies import render_anomalies_view
from cyberguard.dashboard.views_geo import render_geo_view
from cyberguard.dashboard.views_profiles import render_profiles_view
from cyberguard.dashboard.views_sql import render_sql_view

# Apply SOC Theme
apply_soc_theme()

@st.cache_data(show_spinner=False)
def load_and_process_pipeline_data() -> pd.DataFrame:
    """Run end-to-end pipeline: ETL -> Threat Rules -> ML Anomaly Engine -> Risk Scoring -> SQLite Ingestion."""
    # 1. ETL & Feature Engineering
    pipeline = ETLPipeline()
    raw_df, _ = pipeline.run()
    
    # 2. Rule-based Threat Evaluation
    threat_engine = ThreatRuleEngine()
    df_threats = threat_engine.evaluate_dataframe(raw_df)
    
    # 3. ML Anomaly Engine
    anomaly_engine = AnomalyEngine()
    df_anom = anomaly_engine.fit_predict(df_threats)
    
    # 4. Risk Engine
    risk_engine = RiskEngine()
    final_df = risk_engine.evaluate_dataframe(df_anom)
    
    # 5. Ingest into SQLite Database
    db_mgr = DatabaseManager()
    db_mgr.ingest_events(final_df)
    
    return final_df

def main():
    render_header()
    
    # Load dataset with caching
    with st.spinner("Initializing CyberGuard AI Engine & Loading Threat Intelligence..."):
        df = load_and_process_pipeline_data()

    # Sidebar Navigation
    st.sidebar.markdown(f'<div style="display:flex; align-items:center; gap:10px; font-size:1.4rem; font-weight:700; margin-bottom:12px;">{APP_LOGO_SVG} CyberGuard SOC</div>', unsafe_allow_html=True)
    st.sidebar.markdown("---")
    
    navigation_option = st.sidebar.radio(
        "Navigation Menu",
        [
            "SOC Executive Overview",
            "Real-Time Incident Explorer",
            "ML Anomaly & Benchmark",
            "Geo & Impossible Travel",
            "User & Device Profiler",
            "SQL Analytical Studio"
        ]
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown(f'<div style="display:flex; align-items:center; gap:8px; font-weight:700; font-size:1.05rem; margin-bottom:10px;">{get_svg_icon("stats", 18)} Dataset Quick Stats</div>', unsafe_allow_html=True)
    st.sidebar.info(
        f"**Total Events**: {len(df):,}\n\n"
        f"**High Risk Alerts**: {len(df[df['risk_score']>=70]):,}\n\n"
        f"**Critical Incidents**: {len(df[df['severity']=='CRITICAL']):,}"
    )

    # Render Active Navigation View
    if navigation_option == "SOC Executive Overview":
        render_overview_view(df)
    elif navigation_option == "Real-Time Incident Explorer":
        render_incidents_view(df)
    elif navigation_option == "ML Anomaly & Benchmark":
        render_anomalies_view(df)
    elif navigation_option == "Geo & Impossible Travel":
        render_geo_view(df)
    elif navigation_option == "User & Device Profiler":
        render_profiles_view(df)
    elif navigation_option == "SQL Analytical Studio":
        render_sql_view()

if __name__ == "__main__":
    main()

