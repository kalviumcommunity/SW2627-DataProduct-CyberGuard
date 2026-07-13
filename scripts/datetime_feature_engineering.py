"""Datetime feature engineering pipeline for transaction analysis.

This script parses transaction timestamp strings with an explicit format,
extracts temporal features, computes customer recency, builds weekly and
day-hour aggregations, and saves plots for temporal analysis.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
OUTPUT_DIR = BASE_DIR / "output"

TIMESTAMP_COLUMN = "transaction_date"
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
RECENCY_THRESHOLD_DAYS = 30


def sample_transactions() -> pd.DataFrame:
    """Return a small transaction sample with full datetime strings."""
    return pd.DataFrame(
        [
            {
                "transaction_id": 1,
                "customer_id": 101,
                "transaction_date": "2025-01-15 14:30:45",
                "amount": 150.50,
                "status": "completed",
            },
            {
                "transaction_id": 2,
                "customer_id": 102,
                "transaction_date": "2025-01-15 18:05:12",
                "amount": 200.00,
                "status": "completed",
            },
            {
                "transaction_id": 3,
                "customer_id": 101,
                "transaction_date": "2025-01-22 09:10:05",
                "amount": 75.25,
                "status": "pending",
            },
            {
                "transaction_id": 4,
                "customer_id": 103,
                "transaction_date": "2025-01-29 21:45:00",
                "amount": 300.00,
                "status": "completed",
            },
            {
                "transaction_id": 5,
                "customer_id": 102,
                "transaction_date": "2025-02-05 11:20:30",
                "amount": 125.75,
                "status": "completed",
            },
            {
                "transaction_id": 6,
                "customer_id": 104,
                "transaction_date": "2025-02-10 08:15:00",
                "amount": 540.10,
                "status": "completed",
            },
            {
                "transaction_id": 7,
                "customer_id": 101,
                "transaction_date": "2025-02-12 14:05:55",
                "amount": 180.00,
                "status": "completed",
            },
            {
                "transaction_id": 8,
                "customer_id": 105,
                "transaction_date": "2025-02-12 19:40:10",
                "amount": 90.00,
                "status": "failed",
            },
        ]
    )


def load_transactions(input_path: Path | None) -> pd.DataFrame:
    """Load transaction data from disk or fall back to a built-in sample."""
    if input_path and input_path.exists():
        df = pd.read_csv(input_path)
        print(f"Loaded transactions from {input_path}")
        return df

    print("Input file not found; using embedded sample transaction data.")
    return sample_transactions()


def normalize_amount(df: pd.DataFrame) -> pd.DataFrame:
    """Convert amount values to numeric for aggregations."""
    df_clean = df.copy()
    if "amount" in df_clean.columns:
        df_clean["amount"] = (
            df_clean["amount"]
            .astype(str)
            .str.replace("$", "", regex=False)
            .str.replace(",", "", regex=False)
            .str.strip()
        )
        df_clean["amount"] = pd.to_numeric(df_clean["amount"], errors="coerce")
    return df_clean


def parse_transaction_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Parse timestamp strings using the required explicit format."""
    if TIMESTAMP_COLUMN not in df.columns:
        raise KeyError(f"Missing required column: {TIMESTAMP_COLUMN}")

    df_parsed = df.copy()
    df_parsed[TIMESTAMP_COLUMN] = pd.to_datetime(
        df_parsed[TIMESTAMP_COLUMN],
        format=TIMESTAMP_FORMAT,
    )

    print(f"Parsed {TIMESTAMP_COLUMN} with format: {TIMESTAMP_FORMAT}")
    print(f"{TIMESTAMP_COLUMN} dtype: {df_parsed[TIMESTAMP_COLUMN].dtype}")
    return df_parsed


def add_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extract day, hour, week, and supporting time-based features."""
    df_features = df.copy()
    df_features["day_of_week"] = df_features[TIMESTAMP_COLUMN].dt.day_name()
    df_features["hour"] = df_features[TIMESTAMP_COLUMN].dt.hour
    df_features["week_num"] = df_features[TIMESTAMP_COLUMN].dt.isocalendar().week.astype(int)
    df_features["month"] = df_features[TIMESTAMP_COLUMN].dt.month_name()
    df_features["is_weekend"] = df_features[TIMESTAMP_COLUMN].dt.dayofweek >= 5
    return df_features


def compute_recency(df: pd.DataFrame, reference_date: pd.Timestamp | None = None) -> pd.DataFrame:
    """Compute days since last purchase per customer and attach it to each row."""
    if "customer_id" not in df.columns:
        raise KeyError("Missing required column: customer_id")

    df_recency = df.copy()
    if reference_date is None:
        reference_date = pd.Timestamp.now().normalize()

    customer_last_purchase = df_recency.groupby("customer_id")[TIMESTAMP_COLUMN].max()
    customer_recency = (reference_date - customer_last_purchase).dt.days
    df_recency["days_since_last_purchase"] = df_recency["customer_id"].map(customer_recency)
    return df_recency


def build_weekly_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Resample transaction values into weekly buckets."""
    df_ts = df.set_index(TIMESTAMP_COLUMN).sort_index()
    weekly_metrics = df_ts.resample("W").agg(
        amount_sum=("amount", "sum"),
        amount_count=("amount", "count"),
        amount_mean=("amount", "mean"),
    )
    return weekly_metrics


def build_day_hour_aggregation(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create day-hour aggregates and a pivot table for heatmap analysis."""
    ordered_days = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    hourly_daily = (
        df.groupby(["day_of_week", "hour"])
        .agg(amount_sum=("amount", "sum"), amount_count=("amount", "count"), amount_mean=("amount", "mean"))
        .reset_index()
    )

    pivot_table = pd.pivot_table(
        df,
        values="amount",
        index="hour",
        columns="day_of_week",
        aggfunc="sum",
    ).reindex(columns=ordered_days)

    return hourly_daily, pivot_table


def save_plots(df: pd.DataFrame, weekly_metrics: pd.DataFrame, pivot_table: pd.DataFrame, output_dir: Path) -> None:
    """Save temporal analysis plots for the assignment submission."""
    output_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    fig, ax = plt.subplots(figsize=(10, 4))
    hour_counts = df.groupby("hour").size().sort_index()
    hour_counts.plot(kind="bar", ax=ax, color="#1f77b4")
    ax.set_title("Transactions by Hour of Day")
    ax.set_xlabel("Hour")
    ax.set_ylabel("Transaction Count")
    fig.tight_layout()
    fig.savefig(output_dir / "hour_distribution.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4))
    weekly_metrics["amount_sum"].plot(ax=ax, marker="o", color="#ff7f0e")
    ax.set_title("Weekly Revenue Trend")
    ax.set_xlabel("Week Ending")
    ax.set_ylabel("Revenue")
    fig.tight_layout()
    fig.savefig(output_dir / "weekly_revenue_trend.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.heatmap(pivot_table.fillna(0), cmap="Blues", ax=ax)
    ax.set_title("Revenue Heatmap by Hour and Day of Week")
    ax.set_xlabel("Day of Week")
    ax.set_ylabel("Hour")
    fig.tight_layout()
    fig.savefig(output_dir / "hour_day_heatmap.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4))
    df["days_since_last_purchase"].dropna().plot(kind="hist", bins=8, ax=ax, color="#2ca02c")
    ax.set_title("Recency Distribution")
    ax.set_xlabel("Days Since Last Purchase")
    ax.set_ylabel("Customer Count")
    fig.tight_layout()
    fig.savefig(output_dir / "recency_distribution.png", dpi=150)
    plt.close(fig)


def summarize_and_print(df: pd.DataFrame, weekly_metrics: pd.DataFrame, hourly_daily: pd.DataFrame, pivot_table: pd.DataFrame) -> None:
    """Print the required validation checks and summary metrics."""
    print("\nDatetime parsing checks")
    print(f"Min date: {df[TIMESTAMP_COLUMN].min()}")
    print(f"Max date: {df[TIMESTAMP_COLUMN].max()}")
    print(f"Days in dataset: {(df[TIMESTAMP_COLUMN].max() - df[TIMESTAMP_COLUMN].min()).days}")
    print(f"Hours with data: {sorted(df['hour'].unique().tolist())}")
    print(f"Weeks in dataset: {df['week_num'].nunique()}")

    print("\nRecency checks")
    print(f"Min days since purchase: {df['days_since_last_purchase'].min()}")
    print(f"Max days since purchase: {df['days_since_last_purchase'].max()}")
    inactive_customers = df.loc[df["days_since_last_purchase"] > RECENCY_THRESHOLD_DAYS, "customer_id"].drop_duplicates().tolist()
    print(f"Customers with no recent activity (> {RECENCY_THRESHOLD_DAYS} days): {inactive_customers}")

    print("\nHourly distribution")
    print(df.groupby("hour").size().sort_index())

    print("\nWeekly revenue")
    print(weekly_metrics["amount_sum"])

    print("\nDay-hour aggregation")
    print(hourly_daily.head(10).to_string(index=False))

    peak_idx = pivot_table.stack().idxmax()
    peak_value = pivot_table.stack().max()
    print(f"\nPeak activity window: hour={peak_idx[0]}, day={peak_idx[1]}, revenue={peak_value}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Datetime feature engineering for transaction analysis")
    parser.add_argument(
        "--input",
        type=str,
        default=str(RAW_DIR / "transactions.csv"),
        help="Path to the raw transaction CSV. Falls back to embedded sample data if missing.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(OUTPUT_DIR),
        help="Directory where processed files and plots will be written.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)

    df = load_transactions(input_path)
    df = normalize_amount(df)
    df = parse_transaction_dates(df)
    df = add_temporal_features(df)
    df = compute_recency(df)

    weekly_metrics = build_weekly_metrics(df)
    hourly_daily, pivot_table = build_day_hour_aggregation(df)

    output_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_dir / "datetime_features.csv", index=False)
    weekly_metrics.to_csv(output_dir / "weekly_metrics.csv")
    hourly_daily.to_csv(output_dir / "hour_day_aggregation.csv", index=False)
    pivot_table.to_csv(output_dir / "hour_day_pivot.csv")

    save_plots(df, weekly_metrics, pivot_table, output_dir)
    summarize_and_print(df, weekly_metrics, hourly_daily, pivot_table)


if __name__ == "__main__":
    main()