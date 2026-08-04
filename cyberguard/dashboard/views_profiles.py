"""
User & Device Behavioral Deep-Dive Profiling View
"""
import streamlit as st
import pandas as pd
from cyberguard.analytics.profiler import BehavioralProfiler
from cyberguard.dashboard.components import render_section_title

def render_profiles_view(df: pd.DataFrame):
    render_section_title("User & Device Behavioral Deep-Dive Profiler", "profiles")
    
    tab_user, tab_device = st.tabs(["User Behavioral Profiles", "Device Type Profiles"])
    
    with tab_user:
        user_profiles = BehavioralProfiler.build_user_profiles(df)
        render_section_title("User Baseline Profiles & Failure Rates", "users")
        st.dataframe(user_profiles.sort_values(by="failure_rate_pct", ascending=False), use_container_width=True)
        
        st.markdown("---")
        render_section_title("Select User Account to Deep-Dive", "search")
        selected_user = st.selectbox("Choose User", sorted(df["username"].unique().tolist()))
        
        user_events = df[df["username"] == selected_user].sort_values(by="timestamp", ascending=False)
        
        u1, u2, u3, u4 = st.columns(4)
        u1.metric("Total User Logins", len(user_events))
        u2.metric("Failed Logins", len(user_events[user_events["status"]=="Failed"]))
        u3.metric("Unique Countries", user_events["country"].nunique())
        u4.metric("Max Peak Risk Score", user_events["risk_score"].max())
        
        st.markdown("##### Full Authentication History for Account")
        st.dataframe(user_events[["timestamp", "ip_address", "country", "city", "status", "device_type", "risk_score", "primary_reason"]], use_container_width=True)

    with tab_device:
        device_profiles = BehavioralProfiler.build_device_profiles(df)
        render_section_title("Device Type Security Profiles", "device")
        st.dataframe(device_profiles, use_container_width=True)

