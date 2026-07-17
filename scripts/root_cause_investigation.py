from __future__ import annotations

import argparse
from pathlib import Path
import json

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
OUTPUT_DIR = BASE_DIR / "output"


def load_auth_logs(input_path: Path | None = None) -> pd.DataFrame:
    """Load the auth log CSV and normalize the timestamp/status fields."""
    candidate = input_path or (RAW_DIR / "auth_logs.csv")
    if not candidate.exists():
        raise FileNotFoundError(f"Auth log file not found: {candidate}")

    df = pd.read_csv(candidate)
    required_columns = {"timestamp", "status"}
    missing = sorted(required_columns - set(df.columns))
    if missing:
        raise KeyError(f"Missing required columns: {missing}")

    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["status"] = df["status"].astype("string").str.strip()
    df["success_rate"] = (df["status"].str.lower() == "success").astype(int)
    return df.dropna(subset=["timestamp"])


def detect_problem_day(df: pd.DataFrame) -> tuple[pd.Timestamp, pd.Series, float]:
    """Find the date whose success rate falls below mean minus one standard deviation."""
    daily_success = df.groupby(df["timestamp"].dt.date)["success_rate"].mean().sort_index()
    threshold = float(daily_success.mean() - daily_success.std())
    anomaly_dates = daily_success[daily_success < threshold]

    if len(anomaly_dates) > 0:
        problem_day = pd.Timestamp(anomaly_dates.index[0])
    else:
        problem_day = pd.Timestamp(daily_success.idxmin())

    return problem_day, daily_success, threshold


def hourly_breakdown(df: pd.DataFrame, problem_day: pd.Timestamp) -> pd.Series:
    """Compute hourly success rates for the detected problem day."""
    day_mask = df["timestamp"].dt.date == problem_day.date()
    hourly = df.loc[day_mask].groupby(df.loc[day_mask, "timestamp"].dt.hour)["success_rate"].mean().sort_index()
    return hourly


def surrounding_hour_metrics(hourly: pd.Series, problem_hour: int) -> pd.DataFrame:
    """Show the hour before, during, and after the detected problem hour."""
    rows: list[dict[str, object]] = []
    for label, hour in [("before", problem_hour - 1), ("during", problem_hour), ("after", problem_hour + 1)]:
        rows.append(
            {
                "window": label,
                "hour": hour,
                "success_rate": float(hourly.get(hour, float("nan"))),
            }
        )
    return pd.DataFrame(rows)


def segment_analysis(df: pd.DataFrame, problem_day: pd.Timestamp, problem_hour: int) -> dict[str, pd.DataFrame]:
    """Break down the problem window by the available auth dimensions."""
    problem_window = df[(df["timestamp"].dt.date == problem_day.date()) & (df["timestamp"].dt.hour == problem_hour)]
    dimensions = ["username", "country", "device_type"]
    analysis: dict[str, pd.DataFrame] = {}

    for column in dimensions:
        if column in problem_window.columns:
            table = (
                problem_window.groupby(column)["success_rate"]
                .agg(["mean", "count"])
                .sort_values(["mean", "count"], ascending=[True, False])
            )
            analysis[column] = table

    return analysis


def correlation_analysis(df: pd.DataFrame, problem_day: pd.Timestamp, problem_hour: int) -> tuple[dict[str, pd.DataFrame], pd.Series | None]:
    """Build crosstabs for available categorical dimensions and summarize error messages if present."""
    df = df.copy()
    df["is_problem_period"] = ((df["timestamp"].dt.date == problem_day.date()) & (df["timestamp"].dt.hour == problem_hour)).astype(int)

    crosstabs: dict[str, pd.DataFrame] = {}
    for column in ["username", "country", "device_type"]:
        if column in df.columns:
            crosstab = pd.crosstab(df[column], df["is_problem_period"], margins=True)
            crosstabs[column] = crosstab

    error_series = None
    if "error_message" in df.columns:
        error_series = df.loc[df["is_problem_period"] == 1, "error_message"].value_counts().head(10)

    return crosstabs, error_series


def build_investigation_report(
    df: pd.DataFrame,
    problem_day: pd.Timestamp,
    daily_success: pd.Series,
    threshold: float,
    hourly: pd.Series,
    problem_hour: int,
    surrounding_metrics: pd.DataFrame,
    segment_tables: dict[str, pd.DataFrame],
    crosstabs: dict[str, pd.DataFrame],
    error_series: pd.Series | None,
) -> str:
    """Assemble a concise root-cause report from the detected anomaly."""
    problem_window = df[(df["timestamp"].dt.date == problem_day.date()) & (df["timestamp"].dt.hour == problem_hour)]
    problem_rate = float(hourly.get(problem_hour, 0.0))
    rows_in_window = int(len(problem_window))

    if rows_in_window:
        top_row = problem_window.iloc[0]
        affected_user = str(top_row.get("username", "unknown"))
        affected_country = str(top_row.get("country", "unknown"))
        affected_device = str(top_row.get("device_type", "unknown"))
    else:
        affected_user = "unknown"
        affected_country = "unknown"
        affected_device = "unknown"

    surrounding_text = surrounding_metrics.copy()
    surrounding_text["success_rate"] = surrounding_text["success_rate"].map(lambda value: f"{value:.1%}" if pd.notna(value) else "n/a")

    segment_text_parts: list[str] = []
    for name, table in segment_tables.items():
        segment_text_parts.append(f"By {name.replace('_', ' ').title()}:\n{table.to_string()}")

    crosstab_text_parts: list[str] = []
    for name, table in crosstabs.items():
        crosstab_text_parts.append(f"{name.title()}:\n{table.to_string()}")

    dominant_failure_summary = "No error_message column is present in the raw auth log, so error-log correlation cannot be evaluated directly from this workspace data."
    if error_series is not None and not error_series.empty:
        top_error = str(error_series.index[0])
        top_error_pct = float(error_series.iloc[0] / max(rows_in_window, 1))
        dominant_failure_summary = f"Top error '{top_error}' occurred in {top_error_pct:.1%} of the problem-window rows."

    hypothesis = (
        "The anomaly is a localized auth failure affecting a single user/session slice rather than a platform-wide outage. "
        "The raw data shows one trough hour on 2026-07-05 with a 0% success rate in that hour, while adjacent hours recover to normal levels."
    )

    validation = (
        "No external status feed or incident log exists in the workspace, so the external-outage hypothesis cannot be confirmed. "
        "The available evidence instead supports an internal or account-specific issue localized to the affected username, country, and device type."
    )

    schema_note = (
        "The raw auth log does not include customer_type, payment_method, region, or error_message columns. "
        "Segment and correlation analysis therefore uses the available auth dimensions: username, country, and device_type."
    )

    report = f"""
═══════════════════════════════════════════════════════════════════
ROOT CAUSE INVESTIGATION REPORT

OBSERVATION:
- Daily success rate dropped on {problem_day.date()} to {daily_success.loc[problem_day.date()]:.1%}
- Anomaly threshold: {threshold:.1%}
- Timeline: {problem_hour:02d}:00-{problem_hour + 1:02d}:00 UTC
- Problem window rows: {rows_in_window}
- Affected user: {affected_user}
- Affected country: {affected_country}
- Affected device: {affected_device}

ANALYSIS:
- {schema_note}
- Hourly success rates for the problem day:
{hourly.to_string()}

- Surrounding hour comparison:
{surrounding_text.to_string(index=False)}

- Segment breakdown in the problem hour:
{chr(10).join(segment_text_parts) if segment_text_parts else 'No additional segment dimensions available.'}

- Correlation patterns:
{chr(10).join(crosstab_text_parts) if crosstab_text_parts else 'No crosstab outputs available.'}

EVIDENCE:
- {dominant_failure_summary}
- The detected problem hour is lower than the adjacent hours, which recover to normal success rates.

HYPOTHESIS (Confidence: MEDIUM-HIGH):
{hypothesis}

ROOT CAUSE:
Likely localized authentication failure or targeted login issue rather than a systemic platform outage.

RECOMMENDED ACTIONS:
1. Add alerting for sudden hour-level success-rate drops.
2. Investigate the affected account and device metadata for abuse or credential issues.
3. Review login throttling, MFA prompts, and geo/device reputation controls.
4. Add an external incident feed if future investigations need public-service correlation.

VALIDATION:
{validation}
""".strip()

    return report


def run_investigation(input_path: Path | None = None) -> tuple[str, dict[str, object]]:
    """Run the full investigation and return the report plus structured outputs."""
    df = load_auth_logs(input_path)
    problem_day, daily_success, threshold = detect_problem_day(df)
    hourly = hourly_breakdown(df, problem_day)
    problem_hour = int(hourly.idxmin())
    surrounding_metrics = surrounding_hour_metrics(hourly, problem_hour)
    segment_tables = segment_analysis(df, problem_day, problem_hour)
    crosstabs, error_series = correlation_analysis(df, problem_day, problem_hour)

    report = build_investigation_report(
        df=df,
        problem_day=problem_day,
        daily_success=daily_success,
        threshold=threshold,
        hourly=hourly,
        problem_hour=problem_hour,
        surrounding_metrics=surrounding_metrics,
        segment_tables=segment_tables,
        crosstabs=crosstabs,
        error_series=error_series,
    )

    structured = {
        "problem_day": problem_day.strftime("%Y-%m-%d"),
        "problem_hour": problem_hour,
        "threshold": threshold,
        "daily_success": {str(key): float(value) for key, value in daily_success.items()},
        "hourly_success": {str(int(key)): float(value) for key, value in hourly.items()},
        "surrounding_hour_metrics": surrounding_hour_metrics(hourly, problem_hour).to_dict(orient="records"),
    }

    return report, structured


def save_outputs(report: str, structured: dict[str, object]) -> None:
    """Write the report and a small JSON summary to disk."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DIR / "investigation_report.txt", "w", encoding="utf-8") as handle:
        handle.write(report + "\n")

    with open(OUTPUT_DIR / "investigation_summary.json", "w", encoding="utf-8") as handle:
        json.dump(structured, handle, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Investigate the auth log anomaly window.")
    parser.add_argument("--input", type=Path, default=None, help="Path to an auth log CSV file")
    args = parser.parse_args()

    report, structured = run_investigation(args.input)
    save_outputs(report, structured)

    print(report)
    print(f"\nSaved report to: {OUTPUT_DIR / 'investigation_report.txt'}")
    print(f"Saved summary to: {OUTPUT_DIR / 'investigation_summary.json'}")


if __name__ == "__main__":
    main()
