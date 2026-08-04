"""
ML Anomaly & Behavioral Model Evaluation Explorer View
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from cyberguard.models.benchmarker import ModelBenchmarker
from cyberguard.dashboard.components import render_section_title

def render_anomalies_view(df: pd.DataFrame):
    render_section_title("Machine Learning Anomaly Detection & Model Benchmark", "anomalies")
    
    st.markdown("""
    This module benchmarks 5 distinct Machine Learning anomaly detection algorithms:
    **Isolation Forest**, **One-Class SVM**, **Local Outlier Factor (LOF)**, **DBSCAN**, and an **MLP Autoencoder**.
    """)
    
    if st.button("Execute Multi-Model ML Benchmark Suite"):
        with st.spinner("Training and benchmarking ML models across authentication feature matrix..."):
            benchmarker = ModelBenchmarker()
            benchmark_df, _ = benchmarker.benchmark_models(df)
            st.success("Benchmarking Completed!")
            render_section_title("Model Comparison Benchmark Results", "zap")
            st.dataframe(benchmark_df, use_container_width=True)

    st.markdown("---")

    col_left, col_right = st.columns(2)
    
    with col_left:
        render_section_title("Anomaly Score vs Travel Speed Scatter Matrix", "target")
        fig_scatter = px.scatter(
            df,
            x="geo_speed_kmh",
            y="anomaly_score",
            color="severity",
            hover_data=["username", "ip_address", "threat_vector"],
            title="Geo Speed vs ML Anomaly Score Distribution",
            color_discrete_map={
                "CRITICAL": "#dc2626",
                "HIGH": "#ea580c",
                "MEDIUM": "#eab308",
                "LOW": "#10b981",
                "INFO": "#3b82f6"
            }
        )
        fig_scatter.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_scatter, use_container_width=True)

    with col_right:
        render_section_title("Anomaly Score Histogram Distribution", "stats")
        fig_hist = px.histogram(
            df,
            x="anomaly_score",
            nbins=30,
            title="Anomaly Score Distribution Density",
            color_discrete_sequence=["#38bdf8"]
        )
        fig_hist.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown("---")
    render_section_title("High Anomaly Outliers (Score >= 0.70)", "incidents")
    anom_df = df[df["anomaly_score"] >= 0.70].sort_values(by="anomaly_score", ascending=False)
    st.dataframe(anom_df[["timestamp", "username", "ip_address", "country", "anomaly_score", "threat_vector", "primary_reason"]], use_container_width=True)

