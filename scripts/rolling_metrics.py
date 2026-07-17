"""Time-series trend and rolling metrics analysis pipeline.

This script implements:
1. Synthetic daily revenue and orders data generation with gaps and trends.
2. Missing data detection and imputation (forward fill and interpolation).
3. Resampling to weekly and monthly Buckets.
4. 7-day and 30-day rolling averages computation.
5. Month-over-Month percentage changes.
6. Cumulative revenue tracking.
7. Trend direction, magnitude, volatility measurement, and business implications report.
"""

from __future__ import annotations

import os
import sys
import io
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Configure standard output to support UTF-8 on Windows environments
# to prevent UnicodeEncodeError for checkmark characters (✓)
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Define directory structures
BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR = BASE_DIR / "output"

# Ensure all directories exist
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate_synthetic_data(seed: int = 42) -> Path:
    """
    Generate synthetic daily revenue and orders dataset.
    
    Includes weekly seasonality (Tuesday ~$45k, Sunday ~$51k, Friday ~$35k),
    an underlying growth trend, random Gaussian noise, a temporary decline event,
    and random missing values (gaps) to demonstrate time-series imputation.
    """
    np.random.seed(seed)
    date_range = pd.date_range(start="2025-01-01", end="2026-06-30", freq="D")
    n_days = len(date_range)
    
    # Base revenue starting at $40,000 with a steady daily uptrend of $25/day
    base_revenue = 40000.0 + (np.arange(n_days) * 25.0)
    
    # Weekly seasonality: Mon=0, Tue=1, Wed=2, Thu=3, Fri=4, Sat=5, Sun=6
    # Targets: Tuesday ~45k, Friday ~35k, Sunday ~51k
    # We define offsets based on a baseline of 40k
    weekly_offsets = {
        0: 2000.0,    # Monday
        1: 5000.0,    # Tuesday (base 40k + 5k = 45k)
        2: 1000.0,    # Wednesday
        3: 0.0,       # Thursday
        4: -5000.0,   # Friday (base 40k - 5k = 35k)
        5: 7000.0,    # Saturday
        6: 11000.0,   # Sunday (base 40k + 11k = 51k)
    }
    
    seasonality = np.array([weekly_offsets[d.weekday()] for d in date_range])
    
    # Gaussian noise (volatility)
    noise = np.random.normal(loc=0.0, scale=3000.0, size=n_days)
    
    # Simulated transient decline event (e.g. price change/competitor move in Oct 2025)
    # Temporary drop of $8,000/day between day 270 (Sep 28) and day 300 (Oct 28), then recovery
    event_mask = (np.arange(n_days) >= 270) & (np.arange(n_days) <= 300)
    event_drop = event_mask * -8000.0
    
    # Combine components to get final raw revenue
    revenue = base_revenue + seasonality + noise + event_drop
    
    # Orders count: roughly correlated with revenue (approx. $400 average order value)
    orders = (revenue / 400.0).astype(int) + np.random.randint(-10, 10, size=n_days)
    # Ensure orders are non-negative
    orders = np.clip(orders, 1, None)
    
    # Create DataFrame
    df = pd.DataFrame({
        "date": date_range,
        "revenue": revenue,
        "orders": orders
    })
    
    # Introduce random missing gaps (15 random days set to NaN) to demonstrate imputation
    missing_indices = np.random.choice(np.arange(n_days), size=15, replace=False)
    df.loc[missing_indices, "revenue"] = np.nan
    df.loc[missing_indices, "orders"] = np.nan
    
    # Save raw daily data
    raw_path = RAW_DIR / "daily_revenue.csv"
    df.to_csv(raw_path, index=False)
    print(f"✓ Generated raw daily revenue dataset at: {raw_path}")
    print(f"  Shape: {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"  Missing values introduced: {len(missing_indices)} rows")
    
    return raw_path


def clean_and_impute_data(raw_path: Path) -> pd.DataFrame:
    """
    Load raw dataset, detect missing values, and apply time-series imputation.
    
    We use linear interpolation for revenue (since it varies continuously)
    and forward-fill for orders (discrete counts, propagating recent rate).
    """
    df = pd.read_csv(raw_path)
    df["date"] = pd.to_datetime(df["date"])
    
    print("\n--- Missing Data Analysis ---")
    null_revenue = df["revenue"].isnull().sum()
    null_orders = df["orders"].isnull().sum()
    print(f"Missing revenue values: {null_revenue}")
    print(f"Missing orders values: {null_orders}")
    
    # Apply interpolation/fill
    # linear interpolation for revenue
    df["revenue"] = df["revenue"].interpolate(method="linear")
    # forward fill for orders, backward fill as fallback for initial rows if empty
    df["orders"] = df["orders"].ffill().bfill()
    # Cast orders back to integer
    df["orders"] = df["orders"].astype(int)
    
    print("✓ Missing values imputed successfully.")
    print(f"Remaining null values: {df.isnull().sum().sum()}")
    
    # Save processed dataset
    processed_path = PROCESSED_DIR / "daily_revenue_processed.csv"
    df.to_csv(processed_path, index=False)
    print(f"✓ Saved processed dataset to: {processed_path}")
    
    return df


def resample_data(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Task 1: Resample daily data to weekly and monthly frequencies.
    
    Compares which period has the highest revenue.
    """
    print("\n--- Task 1: Resampling Data by Time Period ---")
    df_ts = df.set_index("date")
    
    # Weekly aggregation
    weekly_revenue = df_ts["revenue"].resample("W").sum()
    weekly_count = df_ts["orders"].resample("W").count()
    # Note: Using count of orders (number of daily logs/records) and mean revenue per day
    weekly_avg = df_ts["revenue"].resample("W").mean()
    
    # Monthly aggregation
    monthly_revenue = df_ts["revenue"].resample("ME").sum()
    monthly_orders = df_ts["orders"].resample("ME").sum()
    monthly_avg = df_ts["revenue"].resample("ME").mean()
    
    print(f"Weekly Revenue shape: {weekly_revenue.shape}")
    print(f"Monthly Revenue shape: {monthly_revenue.shape}")
    
    # Identify which month/week has the highest revenue
    max_week = weekly_revenue.idxmax()
    max_month = monthly_revenue.idxmax()
    
    print(f"Highest Revenue Week: {max_week.strftime('%Y-%m-%d')} (${weekly_revenue[max_week]:,.2f})")
    print(f"Highest Revenue Month: {max_month.strftime('%B %Y')} (${monthly_revenue[max_month]:,.2f})")
    
    # Create weekly summary DataFrame
    weekly_df = pd.DataFrame({
        "revenue_sum": weekly_revenue,
        "orders_count": weekly_count,
        "revenue_mean": weekly_avg
    })
    
    # Create monthly summary DataFrame
    monthly_df = pd.DataFrame({
        "revenue_sum": monthly_revenue,
        "orders_sum": monthly_orders,
        "revenue_mean": monthly_avg
    })
    
    return df_ts, weekly_df, monthly_df


def compute_rolling_averages(df: pd.DataFrame) -> pd.DataFrame:
    """
    Task 2: Compute 7-day and 30-day rolling averages and plot raw vs rolling.
    """
    print("\n--- Task 2: Computing Rolling Window Averages ---")
    df_copy = df.copy()
    
    df_copy["revenue_ma7"] = df_copy["revenue"].rolling(window=7, min_periods=1).mean()
    df_copy["revenue_ma30"] = df_copy["revenue"].rolling(window=30, min_periods=1).mean()
    
    # Premium styled plot
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    fig, ax = plt.subplots(figsize=(14, 7), dpi=150)
    
    ax.plot(df_copy["date"], df_copy["revenue"], label="Raw Daily Revenue", color="#00f2fe", alpha=0.3, linewidth=1)
    ax.plot(df_copy["date"], df_copy["revenue_ma7"], label="7-Day Rolling Average (Smooth)", color="#ff007f", alpha=0.9, linewidth=1.8)
    ax.plot(df_copy["date"], df_copy["revenue_ma30"], label="30-Day Rolling Average (Trend)", color="#4facfe", alpha=1.0, linewidth=2.5)
    
    # Formatting
    ax.set_title("Daily Revenue vs. Rolling Averages (Smoothing Daily Noise)", fontsize=16, fontweight="bold", pad=20, color="#1e293b")
    ax.set_xlabel("Timeline", fontsize=12, labelpad=10, color="#475569")
    ax.set_ylabel("Revenue ($ USD)", fontsize=12, labelpad=10, color="#475569")
    
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))
    ax.tick_params(colors="#475569", labelsize=10)
    
    # Highlight the transient decline event in Oct 2025
    # Day 270 (2025-09-28) to Day 300 (2025-10-28)
    ax.axvspan(pd.Timestamp("2025-09-28"), pd.Timestamp("2025-10-28"), color="#cbd5e1", alpha=0.25, label="Transient Decline Event")
    
    ax.legend(frameon=True, facecolor="white", edgecolor="#e2e8f0", fontsize=11, loc="upper left")
    plt.tight_layout()
    
    plot_path = OUTPUT_DIR / "rolling_avg.png"
    plt.savefig(plot_path, facecolor="white", bbox_inches="tight")
    plt.close()
    print(f"✓ Saved rolling averages plot to: {plot_path}")
    
    return df_copy


def calculate_mom_changes(monthly_df: pd.DataFrame) -> pd.Series:
    """
    Task 3: Compute month-over-month percentage change and document growth vs decline.
    """
    print("\n--- Task 3: Month-over-Month Percentage Change ---")
    
    # Compute MoM change
    mom_change = monthly_df["revenue_sum"].pct_change() * 100
    
    # Create output string with detailed summary of growth vs decline
    growth_months = mom_change[mom_change > 0]
    decline_months = mom_change[mom_change < 0]
    
    print("\nGrowth Months (>0% MoM):")
    for date, val in growth_months.items():
        print(f"  {date.strftime('%B %Y')}: {val:+.1f}%")
        
    print("\nDecline Months (<0% MoM):")
    for date, val in decline_months.items():
        print(f"  {date.strftime('%B %Y')}: {val:+.1f}%")
        
    return mom_change


def compute_cumulative_sum(df: pd.DataFrame) -> pd.DataFrame:
    """
    Task 4: Compute cumulative revenue and visualize it.
    """
    print("\n--- Task 4: Computing Cumulative Sum ---")
    df_copy = df.copy()
    
    # Running total of revenue and orders
    df_copy["cumulative_revenue"] = df_copy["revenue"].cumsum()
    df_copy["cumulative_orders"] = df_copy["orders"].cumsum()
    
    # Plot cumulative growth
    fig, ax = plt.subplots(figsize=(14, 6), dpi=150)
    ax.fill_between(df_copy["date"], df_copy["cumulative_revenue"], color="#4facfe", alpha=0.15)
    ax.plot(df_copy["date"], df_copy["cumulative_revenue"], color="#00f2fe", linewidth=3, label="Cumulative Revenue")
    
    ax.set_title("Cumulative Company Revenue Over Time (Aggregated Growth)", fontsize=16, fontweight="bold", pad=20, color="#1e293b")
    ax.set_xlabel("Timeline", fontsize=12, labelpad=10, color="#475569")
    ax.set_ylabel("Total Revenue ($ USD)", fontsize=12, labelpad=10, color="#475569")
    
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))
    ax.tick_params(colors="#475569", labelsize=10)
    ax.legend(frameon=True, facecolor="white", edgecolor="#e2e8f0", fontsize=11, loc="upper left")
    
    plt.tight_layout()
    plot_path = OUTPUT_DIR / "cumulative.png"
    plt.savefig(plot_path, facecolor="white", bbox_inches="tight")
    plt.close()
    
    total_rev = df_copy["cumulative_revenue"].iloc[-1]
    total_orders = df_copy["cumulative_orders"].iloc[-1]
    print(f"✓ Saved cumulative revenue plot to: {plot_path}")
    print(f"Total Revenue Accumulated: ${total_rev:,.2f}")
    print(f"Total Orders Accumulated: {total_orders:,}")
    
    return df_copy


def identify_trends_and_implications(df: pd.DataFrame, mom_change: pd.Series) -> None:
    """
    Task 5: Connect trend observations to business insights and write to output file.
    """
    print("\n--- Task 5: Trend Pattern and Business Implications ---")
    
    # Analyze rolling average trend (last 30 days)
    recent_ma30 = df["revenue_ma30"].iloc[-30:]
    
    # Compare latest value to value 30 days ago
    start_val = recent_ma30.iloc[0]
    end_val = recent_ma30.iloc[-1]
    
    trend_direction = "UPTREND" if end_val > start_val else "DOWNTREND" if end_val < start_val else "FLAT"
    trend_magnitude = ((end_val - start_val) / start_val) * 100
    
    # Last month's MoM growth rate
    latest_mom = mom_change.iloc[-1]
    
    # Volatility measure (noise)
    daily_std = df["revenue"].std()
    avg_daily_rev = df["revenue"].mean()
    coefficient_of_variation = (daily_std / avg_daily_rev) * 100
    
    # Format business interpretation
    business_implication = (
        "Accelerating growth - The underlying business momentum is positive and sustainable. "
        "Maintain current operational strategy and scale marketing spend, ignoring short-term daily variance."
        if trend_direction == "UPTREND" else
        "Declining momentum - Investigate potential structural changes, customer churn, "
        "or efficacy of recent price promotions to reverse the downward trend."
    )
    
    suggested_action = (
        "1. Scale user acquisition: Capitalize on the positive momentum by increasing budgets for high-performing channels.\n"
        "2. Keep the pricing steady: Avoid unnecessary discounting since the underlying trend is strong and positive.\n"
        "3. Focus on retention: Build loyalty loops to maintain the acceleration."
        if trend_direction == "UPTREND" else
        "1. Audit recent product and pricing changes: Determine if the decline aligns with recent billing adjustments.\n"
        "2. Address retention: Launch targeted email re-engagement flows to prevent further contraction.\n"
        "3. Temporary promotional pricing: Utilize short-term campaigns to boost customer velocity."
    )
    
    if trend_direction == "UPTREND":
        impact_text = (
            "Relying on raw daily figures would trigger false alarms (such as Friday's "
            "dip to $35k), prompting reactive discounting. However, the rolling metric "
            "verifies that demand is actually accelerating over time."
        )
    else:
        impact_text = (
            "Relying on raw daily figures might mask a gradual decline because occasional "
            "spikes (like Sunday's $51k) suggest strong health. The 30-day rolling average "
            "filters this noise to reveal a genuine deceleration in business momentum, "
            "requiring proactive strategic adjustments."
        )

    analysis_text = f"""============================================================
TIME-SERIES TREND & BUSINESS IMPLICATIONS REPORT
============================================================

1. TREND DIRECTION AND MAGNITUDE
------------------------------------------------------------
- 30-Day Rolling Average Trend: {trend_direction}
- Revenue growth magnitude over last 30 days: {trend_magnitude:+.2f}%
- Month-over-Month growth rate (latest month): {latest_mom:+.2f}%

2. NOISE VS. SIGNAL ANALYSIS
------------------------------------------------------------
- Average Daily Revenue: ${avg_daily_rev:,.2f}
- Daily Revenue Volatility (Std Dev): ${daily_std:,.2f}
- Volatility Coefficient (Noise Level): {coefficient_of_variation:.1f}%
- Insight: The daily noise ({coefficient_of_variation:.1f}%) is significant.
  A single daily drop (e.g. from $51k to $35k) does not indicate a structural
  decline. Relying on the 30-day moving average filters out this daily noise,
  revealing a clear {trend_direction.lower()} trend.

3. BUSINESS IMPLICATIONS
------------------------------------------------------------
- Status: {business_implication}
- Impact: {impact_text}

4. SUGGESTED ACTION PLAN
------------------------------------------------------------
{suggested_action}

============================================================
Generated by Antigravity Time-Series Pipeline | {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    print(analysis_text)
    
    # Save trend analysis
    output_path = OUTPUT_DIR / "trend_analysis.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(analysis_text)
    print(f"✓ Saved trend analysis report to: {output_path}")


def main():
    print("============================================================")
    print("STARTING TIME-SERIES AND ROLLING METRICS DATA WORKFLOW")
    print("============================================================")
    
    # Generate data
    raw_path = generate_synthetic_data()
    
    # Clean & impute gaps
    df_clean = clean_and_impute_data(raw_path)
    
    # Task 1: Resample
    df_ts, weekly_df, monthly_df = resample_data(df_clean)
    
    # Task 2: Rolling Average
    df_rolling = compute_rolling_averages(df_clean)
    
    # Task 3: MoM Changes
    mom_change = calculate_mom_changes(monthly_df)
    
    # Task 4: Cumulative sum
    df_cumulative = compute_cumulative_sum(df_clean)
    
    # Task 5: Trend & Implications
    identify_trends_and_implications(df_rolling, mom_change)
    
    print("\n============================================================")
    print("WORKFLOW COMPLETED SUCCESSFULLY!")
    print("============================================================")


if __name__ == "__main__":
    main()
