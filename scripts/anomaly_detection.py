from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR = BASE_DIR / "output"

ALERT_RULES = {
    "daily_revenue": {"min": 5000, "max": 50000},
    "transaction_count": {"min": 100, "max": 10000},
    "signup_rate": {"min": 10, "max": 500},
}


def load_daily_revenue(input_path: Path | None = None) -> pd.DataFrame:
    """Load daily revenue data and normalize the date/revenue columns."""
    candidate = input_path or (PROCESSED_DIR / "daily_revenue_processed.csv")
    if not candidate.exists():
        candidate = RAW_DIR / "daily_revenue.csv"

    if not candidate.exists():
        raise FileNotFoundError(f"Daily revenue file not found: {candidate}")

    df = pd.read_csv(candidate)
    required_columns = {"date", "revenue", "orders"}
    missing = sorted(required_columns - set(df.columns))
    if missing:
        raise KeyError(f"Missing required columns: {missing}")

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
    df["orders"] = pd.to_numeric(df["orders"], errors="coerce")
    df = df.dropna(subset=["date"])
    return df.sort_values("date").reset_index(drop=True)


def check_thresholds(metrics: dict[str, float], rules: dict[str, dict[str, float]]) -> list[dict[str, object]]:
    """Alert if metrics are outside business thresholds."""
    alerts: list[dict[str, object]] = []
    for metric_name, rule in rules.items():
        if metric_name not in metrics:
            continue

        value = float(metrics[metric_name])
        if value < rule["min"]:
            alerts.append(
                {
                    "metric": metric_name,
                    "value": value,
                    "threshold": rule["min"],
                    "direction": "BELOW_MIN",
                    "severity": "HIGH",
                }
            )
        elif value > rule["max"]:
            alerts.append(
                {
                    "metric": metric_name,
                    "value": value,
                    "threshold": rule["max"],
                    "direction": "ABOVE_MAX",
                    "severity": "MEDIUM",
                }
            )

    return alerts


def detect_anomalies_zscore(series: pd.Series, threshold: float = 2.0) -> tuple[pd.Series, pd.Series, float, float]:
    """Flag values more than N standard deviations from the mean."""
    clean_series = pd.to_numeric(series, errors="coerce").dropna()
    mean = float(clean_series.mean())
    std = float(clean_series.std(ddof=1))

    if std == 0 or np.isnan(std):
        z_scores = pd.Series(0.0, index=clean_series.index)
        anomalies = clean_series.iloc[0:0]
        return anomalies, z_scores, mean, std

    z_scores = ((clean_series - mean) / std).abs()
    anomalies = clean_series[z_scores > threshold]
    return anomalies, z_scores, mean, std


def classify_severity(value: float, mean: float, std: float) -> str:
    """Classify anomaly severity based on deviation."""
    if std == 0 or np.isnan(std):
        return "LOW"

    z_score = abs((value - mean) / std)
    if z_score > 3:
        return "CRITICAL"
    if z_score > 2:
        return "HIGH"
    if z_score > 1.5:
        return "MEDIUM"
    return "LOW"


def build_anomaly_log(anomalies: pd.Series, z_scores: pd.Series, mean: float, std: float, metric_name: str = "daily_revenue") -> pd.DataFrame:
    """Create a persistent audit trail for detected anomalies."""
    anomaly_log: list[dict[str, object]] = []
    expected_low = mean - 2 * std
    expected_high = mean + 2 * std

    for date, value in anomalies.items():
        severity = classify_severity(float(value), mean, std)
        anomaly_log.append(
            {
                "timestamp": pd.Timestamp.now(),
                "anomaly_date": pd.Timestamp(date),
                "metric": metric_name,
                "value": float(value),
                "expected_range": f"{expected_low:.0f}-{expected_high:.0f}",
                "z_score": float(z_scores.loc[date]),
                "severity": severity,
                "status": "OPEN",
            }
        )

    return pd.DataFrame(anomaly_log)


def save_anomaly_log(anomalies_df: pd.DataFrame, output_dir: Path = OUTPUT_DIR) -> Path:
    """Persist the anomaly audit trail to CSV."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "anomalies_log.csv"
    anomalies_df.to_csv(output_path, index=False)
    return output_path


def prepare_metrics(df: pd.DataFrame) -> dict[str, float]:
    """Build a simple metrics dictionary for threshold checks using the latest day."""
    latest_day = df.sort_values("date").iloc[-1]
    return {
        "daily_revenue": float(latest_day["revenue"]),
        "transaction_count": float(latest_day["orders"]),
        "signup_rate": float(latest_day["orders"]),
    }


def classify_series_anomalies(daily_revenue: pd.Series, threshold: float = 2.0) -> pd.DataFrame:
    """Detect z-score anomalies and assign severity labels."""
    anomalies, z_scores, mean, std = detect_anomalies_zscore(daily_revenue, threshold=threshold)
    rows: list[dict[str, object]] = []
    for date, value in anomalies.items():
        severity = classify_severity(float(value), mean, std)
        rows.append(
            {
                "date": pd.Timestamp(date),
                "value": float(value),
                "z_score": float(z_scores.loc[date]),
                "severity": severity,
            }
        )

    severity_df = pd.DataFrame(rows)
    return severity_df.sort_values(["severity", "date"], ascending=[True, True]).reset_index(drop=True)


def plot_anomalies(daily_revenue: pd.Series, anomalies: pd.Series, output_dir: Path = OUTPUT_DIR) -> Path:
    """Plot raw data, rolling average, expected range, and flagged anomalies."""
    output_dir.mkdir(parents=True, exist_ok=True)
    mean = float(daily_revenue.mean())
    std = float(daily_revenue.std(ddof=1))
    rolling_avg = daily_revenue.rolling(window=7, min_periods=1).mean()

    fig, ax = plt.subplots(figsize=(14, 6), dpi=150)

    ax.plot(daily_revenue.index, daily_revenue.values, marker="o", label="Daily Revenue", linewidth=2, color="#1f77b4")
    ax.plot(rolling_avg.index, rolling_avg.values, label="7-day MA", color="green", linewidth=2)
    ax.fill_between(daily_revenue.index, mean - 2 * std, mean + 2 * std, alpha=0.2, color="blue", label="Expected Range ±2σ")

    for date, value in anomalies.items():
        ax.scatter(date, value, color="red", s=200, marker="X", zorder=5)
        ax.annotate(
            "ANOMALY",
            (date, value),
            xytext=(0, 10),
            textcoords="offset points",
            ha="center",
            fontweight="bold",
            color="red",
        )

    ax.set_xlabel("Date")
    ax.set_ylabel("Revenue ($)")
    ax.set_title("Daily Revenue with Anomalies Flagged")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()

    output_path = output_dir / "anomaly_detection.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return output_path


def run_anomaly_detection(input_path: Path | None = None) -> dict[str, object]:
    """Run threshold and z-score anomaly detection on daily revenue."""
    df = load_daily_revenue(input_path)
    metrics = prepare_metrics(df)
    threshold_alerts = check_thresholds(metrics, ALERT_RULES)

    daily_revenue = df.set_index("date")["revenue"].tail(30)
    anomalies, z_scores, mean, std = detect_anomalies_zscore(daily_revenue, threshold=2)
    severity_df = classify_series_anomalies(daily_revenue, threshold=2)
    high_severity = severity_df[severity_df["severity"].isin(["CRITICAL", "HIGH"])] if not severity_df.empty else severity_df
    anomaly_log = build_anomaly_log(anomalies, z_scores, mean, std)
    anomaly_log_path = save_anomaly_log(anomaly_log)
    plot_path = plot_anomalies(daily_revenue, anomalies)

    return {
        "metrics": metrics,
        "threshold_alerts": threshold_alerts,
        "daily_revenue": daily_revenue,
        "anomalies": anomalies,
        "z_scores": z_scores,
        "mean": mean,
        "std": std,
        "severity_df": severity_df,
        "high_severity": high_severity,
        "anomaly_log_path": anomaly_log_path,
        "plot_path": plot_path,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Threshold and z-score anomaly detection for daily revenue.")
    parser.add_argument("--input", type=Path, default=None, help="Optional CSV path for daily revenue data")
    args = parser.parse_args()

    result = run_anomaly_detection(args.input)

    print("Threshold alerts:")
    if result["threshold_alerts"]:
        for alert in result["threshold_alerts"]:
            print(f"- {alert['metric']} {alert['direction']}: {alert['value']} (threshold {alert['threshold']})")
    else:
        print("- No threshold alerts")

    anomalies = result["anomalies"]
    z_scores = result["z_scores"]
    print(f"\nDetected {len(anomalies)} anomalies out of {len(result['daily_revenue'])} days")
    for date, value in anomalies.items():
        print(f"  {date.date()}: ${value:.0f} (z-score: {z_scores.loc[date]:.2f})")

    severity_df = result["severity_df"]
    print("\nSeverity classification:")
    print(severity_df)
    print(f"\n⚠️ {len(result['high_severity'])} critical anomalies require investigation")
    print(f"Logged anomalies to: {result['anomaly_log_path']}")
    print(f"Saved visualization to: {result['plot_path']}")


if __name__ == "__main__":
    main()
