"""
SQL Analytical Studio & Window Function Query View
"""
import streamlit as st
import pandas as pd
from cyberguard.sql.db_manager import DatabaseManager
from cyberguard.sql.queries import WINDOW_VELOCITY_QUERY, BRUTE_FORCE_SQL, USER_RISK_RANKING_SQL
from cyberguard.dashboard.components import render_section_title

def render_sql_view():
    render_section_title("SQL Analytical Studio & Database Views", "sql")
    
    db_mgr = DatabaseManager()
    
    st.markdown("""
    Execute high-performance SQLite queries utilizing normalized database tables (`auth_events`, `users`, `devices`, `risk_alerts`)
    and analytical views (`v_user_risk_summary`, `v_threat_timeline`).
    """)
    
    query_option = st.selectbox(
        "Select Sample Analytical SQL Query",
        [
            "Custom Query",
            "Window Function: Authentication Velocity & Lagged Location",
            "Brute Force Pattern Aggregation",
            "User Security Risk Ranking (Dense Rank)",
            "View: v_user_risk_summary",
            "View: v_threat_timeline"
        ]
    )
    
    default_query = "SELECT * FROM auth_events LIMIT 20;"
    if query_option == "Window Function: Authentication Velocity & Lagged Location":
        default_query = WINDOW_VELOCITY_QUERY
    elif query_option == "Brute Force Pattern Aggregation":
        default_query = BRUTE_FORCE_SQL
    elif query_option == "User Security Risk Ranking (Dense Rank)":
        default_query = USER_RISK_RANKING_SQL
    elif query_option == "View: v_user_risk_summary":
        default_query = "SELECT * FROM v_user_risk_summary ORDER BY max_risk_score DESC;"
    elif query_option == "View: v_threat_timeline":
        default_query = "SELECT * FROM v_threat_timeline LIMIT 50;"

    sql_input = st.text_area("SQL Query Input", value=default_query, height=180)
    
    if st.button("Execute SQL Query"):
        try:
            res_df = db_mgr.execute_query(sql_input)
            st.success(f"Query returned {len(res_df):,} rows.")
            st.dataframe(res_df, use_container_width=True)
        except Exception as e:
            st.error(f"SQL Execution Error: {str(e)}")

