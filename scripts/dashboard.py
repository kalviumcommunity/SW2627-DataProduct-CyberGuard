import streamlit as st
import sqlite3
import pandas as pd
import os
from dotenv import load_dotenv

# Set page config for a premium wide layout
st.set_page_config(
    page_title="CyberGuard SOC Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load configuration
load_dotenv()
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/cyberguard.db")

# Custom CSS for glassmorphism / premium dark look
st.markdown("""
<style>
    .main {
        background-color: #0f111a;
        color: #ffffff;
    }
    .stMetric {
        background-color: #1a1d2e;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #2e344e;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    .css-1r6g72d {
        color: #00ffcc !important;
    }
    h1, h2, h3 {
        font-family: 'Outfit', 'Inter', sans-serif;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    .title-text {
        background: linear-gradient(90deg, #00f2fe 0%, #4facfe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
</style>
""", unsafe_allow_html=True)

def load_data():
    """Load data from the SQLite database."""
    if not os.path.exists(DATABASE_PATH):
        st.error(f"Database not found at {DATABASE_PATH}. Please run the pipeline script first.")
        return None, None
        
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        events_df = pd.read_sql_query("SELECT * FROM auth_events", conn)
        profiles_df = pd.read_sql_query("SELECT * FROM user_risk_profiles", conn)
        conn.close()
        return events_df, profiles_df
    except Exception as e:
        st.error(f"Error reading database: {str(e)}")
        return None, None

def main():
    # Sidebar Configuration
    st.sidebar.image("https://img.icons8.com/nolan/96/shield.png", width=80)
    st.sidebar.markdown("# 🛡️ CyberGuard SOC")
    st.sidebar.markdown("---")
    
    events_df, profiles_df = load_data()
    
    if events_df is None or profiles_df is None:
        st.info("Execute: `python scripts/pipeline.py` to populate data.")
        return

    # Sidebar filters
    st.sidebar.subheader("Filters")
    selected_user = st.sidebar.selectbox("Filter by User", ["All"] + sorted(events_df["username"].unique().tolist()))
    selected_status = st.sidebar.multiselect("Filter by Status", ["Success", "Failed"], default=["Success", "Failed"])
    
    # Filter Data
    filtered_events = events_df.copy()
    if selected_user != "All":
        filtered_events = filtered_events[filtered_events["username"] == selected_user]
    if selected_status:
        filtered_events = filtered_events[filtered_events["status"].isin(selected_status)]

    # Main dashboard UI
    st.markdown('<h1 class="title-text">🛡️ CyberGuard Security Operations Center</h1>', unsafe_allow_html=True)
    st.markdown("### Production Real-time Authentication Threat Intel & Behavioral Analysis")
    st.markdown("---")
    
    # KPIs Row
    col1, col2, col3, col4 = st.columns(4)
    
    total_events = len(filtered_events)
    failed_logins = len(filtered_events[filtered_events["status"] == "Failed"])
    failure_rate = (failed_logins / total_events * 100) if total_events > 0 else 0.0
    high_risk_alerts = len(filtered_events[filtered_events["risk_score"] >= 70])
    
    col1.metric("Total Login Attempts", f"{total_events:,}")
    col2.metric("Failed Attempts", f"{failed_logins:,}")
    col3.metric("Failure Rate", f"{failure_rate:.1f}%")
    col4.metric("High-Risk Alerts (Risk >= 70)", f"{high_risk_alerts:,}", delta_color="inverse")
    
    st.markdown("###")
    
    # Detailed layouts
    tab1, tab2, tab3 = st.tabs(["🚨 Alerts & Threat Log", "👤 User Risk Profiles", "📊 Analytics & Country Dist"])
    
    with tab1:
        st.subheader("Critical Alerts & High-Risk Incidents (Score >= 70)")
        high_risk_df = filtered_events[filtered_events["risk_score"] >= 70].sort_values(by="risk_score", ascending=False)
        if not high_risk_df.empty:
            st.dataframe(high_risk_df, use_container_width=True)
        else:
            st.success("No high-risk security alerts detected in the filtered log.")
            
        st.markdown("---")
        st.subheader("All Ingested Authentication Events")
        st.dataframe(filtered_events.sort_values(by="timestamp", ascending=False), use_container_width=True)
        
    with tab2:
        st.subheader("User Behavioral Profiles & Risk Scoring")
        st.markdown("Aggregated risk profiles calculated during pipeline execution:")
        st.dataframe(profiles_df.sort_values(by="max_risk_score", ascending=False), use_container_width=True)
        
    with tab3:
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("Failed Logins by Country")
            failed_country_counts = filtered_events[filtered_events["status"] == "Failed"]["country"].value_counts().reset_index()
            failed_country_counts.columns = ["Country", "Failed Logins"]
            if not failed_country_counts.empty:
                st.bar_chart(failed_country_counts.set_index("Country"))
            else:
                st.info("No failed logins to chart.")
                
        with col_right:
            st.subheader("Risk Score Distribution")
            if not filtered_events.empty:
                # Group risk score into buckets
                filtered_events["risk_bucket"] = pd.cut(
                    filtered_events["risk_score"], 
                    bins=[0, 30, 70, 100], 
                    labels=["Low (0-30)", "Medium (31-69)", "High (70-100)"]
                )
                bucket_counts = filtered_events["risk_bucket"].value_counts().reset_index()
                bucket_counts.columns = ["Risk Category", "Incident Count"]
                st.bar_chart(bucket_counts.set_index("Risk Category"))
            else:
                st.info("No events to analyze risk distribution.")

if __name__ == "__main__":
    main()
