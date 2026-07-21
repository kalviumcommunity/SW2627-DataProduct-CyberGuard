from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st


st.set_page_config(page_title="Business Performance Dashboard", layout="wide")


PALETTE = {
    "primary": "#1f77b4",
    "secondary": "#ff7f0e",
    "success": "#2ca02c",
    "danger": "#d62728",
    "neutral": "#7f8c8d",
    "bg": "#0f172a",
    "panel": "#111827",
    "border": "#334155",
    "text": "#f8fafc",
}


st.markdown(
    f"""
    <style>
        .main {{
            background: linear-gradient(180deg, {PALETTE['bg']} 0%, #111827 100%);
            color: {PALETTE['text']};
        }}
        h1, h2, h3, h4 {{
            color: {PALETTE['text']};
        }}
        .stMetric {{
            background: {PALETTE['panel']};
            border: 1px solid {PALETTE['border']};
            border-radius: 12px;
            padding: 14px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


def build_demo_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    months = pd.date_range("2024-01-01", periods=12, freq="M")
    revenue = np.array([4.2, 4.5, 4.8, 4.6, 5.0, 5.1, 4.9, 4.7, 5.2, 5.4, 5.5, 5.2])
    active_customers = np.array([2100, 2160, 2200, 2235, 2290, 2340, 2385, 2430, 2485, 2525, 2560, 2600])
    churned_customers = np.array([95, 90, 92, 88, 84, 81, 79, 77, 74, 72, 70, 68])
    campaign_conversions = np.array([280, 295, 310, 303, 330, 338, 325, 318, 347, 359, 366, 351])
    marketing_spend = np.array([1.25, 1.3, 1.28, 1.22, 1.35, 1.38, 1.33, 1.29, 1.41, 1.44, 1.47, 1.39])
    nps = np.array([67, 68, 68, 69, 70, 70, 71, 71, 72, 73, 73, 72])

    trend_df = pd.DataFrame(
        {
            "month": months,
            "revenue_m": revenue,
            "active_customers": active_customers,
            "churned_customers": churned_customers,
            "campaign_conversions": campaign_conversions,
            "marketing_spend_m": marketing_spend,
            "nps": nps,
        }
    )

    segment_df = pd.DataFrame(
        {
            "segment": ["Enterprise", "Mid-Market", "SMB", "Starter"],
            "revenue_m": [2.1, 1.5, 1.0, 0.6],
            "conversion_rate": [18.5, 14.8, 11.2, 7.4],
        }
    )

    region_df = pd.DataFrame(
        {
            "region": ["North America", "Europe", "APAC", "LATAM"],
            "revenue_m": [2.4, 1.6, 1.1, 0.7],
            "campaign_roi": [3.8, 3.2, 2.9, 2.4],
        }
    )

    detail_rows = []
    segments = ["Enterprise", "Mid-Market", "SMB", "Starter"]
    regions = ["North America", "Europe", "APAC", "LATAM"]
    campaigns = ["Spring Launch", "Retention Push", "Partner Promo", "Upsell Q4"]
    rng = np.random.default_rng(42)

    for index, month in enumerate(months):
        for row_number in range(8):
            segment = segments[(index + row_number) % len(segments)]
            region = regions[(index + row_number) % len(regions)]
            campaign = campaigns[(index + row_number) % len(campaigns)]
            revenue_value = round(float(rng.uniform(1200, 28000)), 2)
            churn_risk = round(float(rng.uniform(0.04, 0.26)), 3)
            detail_rows.append(
                {
                    "customer_id": f"C-{index:02d}{row_number:02d}",
                    "segment": segment,
                    "region": region,
                    "campaign": campaign,
                    "revenue": revenue_value,
                    "last_activity": month + pd.offsets.Day(row_number * 2),
                    "churn_risk": churn_risk,
                }
            )

    detail_df = pd.DataFrame(detail_rows)
    detail_df["last_activity"] = pd.to_datetime(detail_df["last_activity"])
    return trend_df, segment_df, region_df, detail_df


def plot_revenue_trend(trend_df: pd.DataFrame) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(trend_df["month"], trend_df["revenue_m"], marker="o", linewidth=2.5, color=PALETTE["primary"])
    ax.axhline(y=5.0, color=PALETTE["success"], linestyle="--", linewidth=1.5, label="Target: $5M")
    ax.annotate(
        "Latest: $5.2M",
        xy=(trend_df["month"].iloc[-1], trend_df["revenue_m"].iloc[-1]),
        xytext=(-80, 18),
        textcoords="offset points",
        arrowprops=dict(arrowstyle="->", color=PALETTE["neutral"]),
        color=PALETTE["text"],
    )
    ax.set_title("Monthly Revenue Trend (2024)", fontsize=14, fontweight="bold")
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue ($M)")
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    return fig


def plot_customer_metrics(trend_df: pd.DataFrame) -> plt.Figure:
    fig, ax1 = plt.subplots(figsize=(12, 5))
    ax1.plot(
        trend_df["month"],
        trend_df["active_customers"],
        marker="o",
        linewidth=2.5,
        color=PALETTE["secondary"],
        label="Active Customers",
    )
    ax1.set_xlabel("Month")
    ax1.set_ylabel("Active Customers", color=PALETTE["secondary"])
    ax1.tick_params(axis="y", labelcolor=PALETTE["secondary"])
    ax1.grid(True, alpha=0.2)

    ax2 = ax1.twinx()
    ax2.plot(
        trend_df["month"],
        trend_df["churned_customers"],
        marker="s",
        linewidth=2.5,
        color=PALETTE["danger"],
        label="Churned Customers",
    )
    ax2.axhline(y=75, color=PALETTE["neutral"], linestyle="--", linewidth=1.2, label="Churn Watchline")
    ax2.set_ylabel("Churned Customers", color=PALETTE["danger"])
    ax2.tick_params(axis="y", labelcolor=PALETTE["danger"])

    ax1.set_title("Customer Base vs Churn Trend", fontsize=14, fontweight="bold")
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper left")
    fig.tight_layout()
    return fig


def plot_campaign_trend(trend_df: pd.DataFrame) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(trend_df["month"], trend_df["campaign_conversions"], marker="o", linewidth=2.5, color=PALETTE["success"])
    ax.set_title("Campaign Conversions Over Time", fontsize=14, fontweight="bold")
    ax.set_xlabel("Month")
    ax.set_ylabel("Conversions")
    ax.axvline(trend_df["month"].iloc[8], color=PALETTE["secondary"], linestyle=":", linewidth=1.6, label="Q4 Campaign Boost")
    ax.annotate(
        "Q4 lift",
        xy=(trend_df["month"].iloc[9], trend_df["campaign_conversions"].iloc[9]),
        xytext=(12, 16),
        textcoords="offset points",
        color=PALETTE["text"],
        arrowprops=dict(arrowstyle="->", color=PALETTE["neutral"]),
    )
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    return fig


def plot_segment_revenue(segment_df: pd.DataFrame) -> plt.Figure:
    colors = [PALETTE["primary"], PALETTE["secondary"], PALETTE["success"], PALETTE["danger"]]
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(segment_df["segment"], segment_df["revenue_m"], color=colors)
    ax.set_xlabel("Revenue ($M)")
    ax.set_title("Revenue by Customer Segment", fontsize=14, fontweight="bold")
    for bar, val in zip(bars, segment_df["revenue_m"]):
        ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2, f"${val:.1f}M", va="center")
    fig.tight_layout()
    return fig


def plot_region_revenue(region_df: pd.DataFrame) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(
        region_df["region"],
        region_df["revenue_m"],
        color=[PALETTE["primary"], PALETTE["secondary"], PALETTE["success"], PALETTE["danger"]],
    )
    ax.set_title("Revenue by Region", fontsize=14, fontweight="bold")
    ax.set_ylabel("Revenue ($M)")
    ax.axhline(region_df["revenue_m"].mean(), color=PALETTE["neutral"], linestyle="--", linewidth=1.2, label="Average Region Revenue")
    for bar, val in zip(bars, region_df["revenue_m"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.04, f"${val:.1f}M", ha="center")
    ax.legend()
    fig.tight_layout()
    return fig


def plot_campaign_roi(region_df: pd.DataFrame) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(region_df["region"], region_df["campaign_roi"], color=PALETTE["secondary"])
    ax.set_xlabel("ROI (x)")
    ax.set_title("Campaign ROI by Region", fontsize=14, fontweight="bold")
    for bar, val in zip(bars, region_df["campaign_roi"]):
        ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2, f"{val:.1f}x", va="center")
    fig.tight_layout()
    return fig


def main() -> None:
    trend_df, segment_df, region_df, detail_df = build_demo_data()

    st.title("Business Performance Dashboard")
    st.caption("Information hierarchy: status at the top, trends in the middle, segment comparisons below, and detail on demand.")

    # Level 1 - KPI summary cards
    revenue_value = trend_df["revenue_m"].iloc[-1]
    revenue_delta = revenue_value - trend_df["revenue_m"].iloc[-2]
    active_value = int(trend_df["active_customers"].iloc[-1])
    active_delta = active_value - int(trend_df["active_customers"].iloc[-2])
    aov_value = 145
    aov_delta = 3
    churn_value = 4.8
    churn_delta = -1.2
    nps_value = int(trend_df["nps"].iloc[-1])
    nps_delta = nps_value - int(trend_df["nps"].iloc[-2])

    kpi_cols = st.columns(5)
    with kpi_cols[0]:
        st.metric("Revenue", f"${revenue_value:.1f}M", delta=f"{revenue_delta:+.1f}M")
    with kpi_cols[1]:
        st.metric("Active Customers", f"{active_value:,}", delta=f"{active_delta:+,}")
    with kpi_cols[2]:
        st.metric("Avg Order Value", f"${aov_value}", delta=f"{aov_delta:+.1f}%")
    with kpi_cols[3]:
        st.metric("Churn Rate", f"{churn_value:.1f}%", delta=f"{churn_delta:+.1f}%", delta_color="inverse")
    with kpi_cols[4]:
        st.metric("NPS Score", f"{nps_value}", delta=f"{nps_delta:+d}")

    st.divider()

    st.subheader("Level 2: Trends")
    trend_cols = st.columns(3)
    with trend_cols[0]:
        st.pyplot(plot_revenue_trend(trend_df), use_container_width=True)
    with trend_cols[1]:
        st.pyplot(plot_customer_metrics(trend_df), use_container_width=True)
    with trend_cols[2]:
        st.pyplot(plot_campaign_trend(trend_df), use_container_width=True)

    st.divider()

    st.subheader("Level 3: Segment Comparisons")
    segment_cols = st.columns(2)
    with segment_cols[0]:
        st.pyplot(plot_region_revenue(region_df), use_container_width=True)
    with segment_cols[1]:
        st.pyplot(plot_segment_revenue(segment_df), use_container_width=True)
        st.pyplot(plot_campaign_roi(region_df), use_container_width=True)

    st.divider()

    st.subheader("Level 4: Detailed Data Explorer")
    detail_cols = st.columns([1, 3])
    with detail_cols[0]:
        st.markdown("**Filters**")
        selected_segment = st.selectbox("Customer Segment", ["All"] + segment_df["segment"].tolist())
        selected_region = st.selectbox("Region", ["All"] + region_df["region"].tolist())
        selected_campaign = st.selectbox("Campaign", ["All"] + sorted(detail_df["campaign"].unique().tolist()))
        start_date = detail_df["last_activity"].min().date()
        end_date = detail_df["last_activity"].max().date()
        selected_dates = st.date_input("Date Range", value=(start_date, end_date))

    filtered_df = detail_df.copy()
    if selected_segment != "All":
        filtered_df = filtered_df[filtered_df["segment"] == selected_segment]
    if selected_region != "All":
        filtered_df = filtered_df[filtered_df["region"] == selected_region]
    if selected_campaign != "All":
        filtered_df = filtered_df[filtered_df["campaign"] == selected_campaign]

    if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
        start_selected = pd.Timestamp(selected_dates[0])
        end_selected = pd.Timestamp(selected_dates[1])
        filtered_df = filtered_df[(filtered_df["last_activity"] >= start_selected) & (filtered_df["last_activity"] <= end_selected)]

    with detail_cols[1]:
        st.write(f"Showing {len(filtered_df):,} records")
        st.dataframe(
            filtered_df[["customer_id", "segment", "region", "campaign", "revenue", "last_activity", "churn_risk"]],
            use_container_width=True,
        )
        csv_data = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name="filtered_data.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()