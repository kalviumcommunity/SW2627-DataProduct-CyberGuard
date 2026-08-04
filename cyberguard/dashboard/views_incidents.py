"""
Real-Time Incident & Threat Event Explorer View
"""
import streamlit as st
import pandas as pd
from cyberguard.reporting.report_generator import SOCReportGenerator
from cyberguard.dashboard.components import render_section_title

def render_incidents_view(df: pd.DataFrame):
    render_section_title("Incident Explorer & Threat Event Log", "incidents")
    
    # Filters Bar
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        severity_filter = st.multiselect(
            "Filter Severity",
            options=["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"],
            default=["CRITICAL", "HIGH", "MEDIUM"]
        )
    with f2:
        status_filter = st.multiselect("Filter Status", options=["Success", "Failed"], default=["Success", "Failed"])
    with f3:
        users = ["All Users"] + sorted(df["username"].unique().tolist())
        selected_user = st.selectbox("Filter Username", users)
    with f4:
        min_risk = st.slider("Minimum Risk Score Threshold", 0, 100, 30)

    # Filter Data
    filtered = df.copy()
    if severity_filter:
        filtered = filtered[filtered["severity"].isin(severity_filter)]
    if status_filter:
        filtered = filtered[filtered["status"].isin(status_filter)]
    if selected_user != "All Users":
        filtered = filtered[filtered["username"] == selected_user]
    filtered = filtered[filtered["risk_score"] >= min_risk]

    # Search Bar
    search_query = st.text_input("Search Events (by IP, Username, Country, or Reason)", "")
    if search_query:
        mask = (
            filtered["username"].str.contains(search_query, case=False, na=False) |
            filtered["ip_address"].str.contains(search_query, case=False, na=False) |
            filtered["country"].str.contains(search_query, case=False, na=False) |
            filtered["primary_reason"].str.contains(search_query, case=False, na=False)
        )
        filtered = filtered[mask]

    st.markdown(f"**Showing {len(filtered):,} matching security events out of {len(df):,} total records.**")
    
    # Incident Table
    display_cols = [
        "timestamp", "username", "ip_address", "country", "status",
        "device_type", "threat_vector", "risk_score", "severity",
        "primary_reason", "recommended_action"
    ]
    available_cols = [c for c in display_cols if c in filtered.columns]
    
    st.dataframe(
        filtered[available_cols].sort_values(by="risk_score", ascending=False),
        use_container_width=True,
        height=450
    )

    # Export Buttons
    render_section_title("Export & Download SOC Reports", "export")
    e1, e2 = st.columns(2)
    
    reporter = SOCReportGenerator()
    
    with e1:
        if st.button("Export Filtered Dataset to CSV"):
            csv_path = reporter.export_csv(filtered)
            with open(csv_path, "rb") as file:
                st.download_button(
                    label="Click to Download CSV Report",
                    data=file,
                    file_name="cyberguard_incidents.csv",
                    mime="text/csv"
                )
                
    with e2:
        if st.button("Generate Executive PDF Report"):
            pdf_path = reporter.generate_pdf_report(filtered)
            with open(pdf_path, "rb") as file:
                st.download_button(
                    label="Click to Download PDF Incident Briefing",
                    data=file,
                    file_name="cyberguard_executive_incident_briefing.pdf",
                    mime="application/pdf"
                )

