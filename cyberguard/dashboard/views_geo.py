"""
Geo Location & Impossible Travel Map Visualizer View
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from cyberguard.dashboard.components import render_section_title

def render_geo_view(df: pd.DataFrame):
    render_section_title("Geographical Threat Intelligence & Impossible Travel Map", "geo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        render_section_title("Global Authentication Origin Map", "geo")
        fig_map = px.scatter_geo(
            df,
            lat="latitude",
            lon="longitude",
            color="status",
            hover_name="country",
            hover_data=["city", "username", "ip_address", "risk_score"],
            title="Global Login Locations",
            color_discrete_map={"Success": "#10b981", "Failed": "#ef4444"},
            projection="natural earth"
        )
        fig_map.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_map, use_container_width=True)

    with col2:
        render_section_title("Failed Authentications Heatmap by Country", "incidents")
        failed_df = df[df["status"] == "Failed"].groupby("country").size().reset_index(name="failed_logins")
        fig_choropleth = px.choropleth(
            failed_df,
            locations="country",
            locationmode="ISO-3",
            color="failed_logins",
            title="Failed Login Intensity by Country",
            color_continuous_scale="Reds"
        )
        fig_choropleth.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_choropleth, use_container_width=True)

    st.markdown("---")

    # Impossible Travel Table & Speed Breakdown
    render_section_title("Flagged Impossible Travel Velocity Incidents", "plane")
    travel_df = df[df.get("flag_impossible_travel", False) == True].sort_values(by="geo_speed_kmh", ascending=False)
    if not travel_df.empty:
        st.dataframe(
            travel_df[[
                "timestamp", "username", "ip_address", "prev_country", "country",
                "time_diff_min", "geo_dist_km", "geo_speed_kmh", "risk_score"
            ]],
            use_container_width=True
        )
    else:
        st.info("No impossible travel velocity incidents flagged in current dataset.")

