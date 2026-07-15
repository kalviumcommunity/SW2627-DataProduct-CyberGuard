"""Revenue distribution analysis for skewness, segments, and business interpretation.

Implements:
1) Distribution plots (histogram + KDE)
2) Skewness and kurtosis statistics
3) Abnormal pattern checks (percentiles, tail gaps)
4) Segment distribution comparison (high-value vs low-value)
5) Business interpretation connected to statistics
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats


BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR = BASE_DIR / "output"

PREFERRED_REVENUE_COLUMNS = ["revenue", "amount", "transaction_amount", "payment.amount", "price", "value"]


def load_dataset(input_path: Path | None = None) -> pd.DataFrame:
    """Load dataset from provided path or choose a sensible project default."""
    if input_path:
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        return pd.read_csv(input_path)

    candidates = [
        RAW_DIR / "raw_data.csv",
        RAW_DIR / "missing_data.csv",
        PROCESSED_DIR / "transactions_ingested.csv",
        PROCESSED_DIR / "typed_data.csv",
    ]
    for candidate in candidates:
        if candidate.exists():
            return pd.read_csv(candidate)

    raise FileNotFoundError("No default input dataset found. Pass --input with a CSV path.")


def prepare_revenue_series(df: pd.DataFrame, preferred_column: str | None = None) -> tuple[pd.Series, str]:
    """Return a cleaned numeric revenue series and the source column name."""
    candidate_columns = [preferred_column] if preferred_column else []
    candidate_columns.extend(PREFERRED_REVENUE_COLUMNS)

    source_column = None
    for col in candidate_columns:
        if col and col in df.columns:
            source_column = col
            break

    if source_column is None:
        raise KeyError(
            "No usable revenue-like column found. Tried: "
            + ", ".join([c for c in candidate_columns if c])
            + ". Available columns: "
            + ", ".join(df.columns.astype(str).tolist())
        )

    revenue = (
        df[source_column]
        .astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
    )
    revenue = pd.to_numeric(revenue, errors="coerce").dropna()

    if revenue.empty:
        raise ValueError(f"Column '{source_column}' has no numeric values after cleaning.")

    revenue.name = "revenue"
    return revenue, source_column


def plot_distribution(revenue: pd.Series, output_dir: Path) -> None:
    """Task 1: Save histogram and KDE for revenue."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].hist(revenue, bins=50, edgecolor="black")
    axes[0].set_title("Revenue Distribution (Histogram)")
    axes[0].set_xlabel("Revenue")

    revenue.plot(kind="density", ax=axes[1])
    axes[1].set_title("Revenue Distribution (KDE)")
    axes[1].set_xlabel("Revenue")

    plt.tight_layout()
    plt.savefig(output_dir / "revenue_distribution.png", dpi=150)
    plt.close(fig)


def compute_moments(revenue: pd.Series) -> tuple[float, float]:
    """Task 2: Compute skewness and kurtosis.

    Uses Pearson kurtosis (normal=3), which aligns with the threshold check.
    """
    skewness = float(stats.skew(revenue, bias=False))
    kurtosis = float(stats.kurtosis(revenue, fisher=False, bias=False))
    return skewness, kurtosis


def abnormal_pattern_report(revenue: pd.Series) -> tuple[pd.Series, dict[str, float]]:
    """Task 3: Describe percentiles and large quantile gaps for hidden-segment hints."""
    percentiles = revenue.quantile([0.25, 0.5, 0.75, 0.9, 0.95, 0.99])
    p75_p90_gap = float(percentiles.loc[0.9] - percentiles.loc[0.75])
    median = float(percentiles.loc[0.5])
    gap_ratio = float((p75_p90_gap / median) if median else 0.0)

    top_1_threshold = float(percentiles.loc[0.99])
    top_1_share = float(revenue[revenue >= top_1_threshold].sum() / revenue.sum()) if revenue.sum() else 0.0

    flags = {
        "p75_p90_gap": p75_p90_gap,
        "gap_ratio_to_median": gap_ratio,
        "top_1pct_revenue_share": top_1_share,
    }
    return percentiles, flags


def compare_segments(revenue: pd.Series, output_dir: Path) -> tuple[pd.Series, pd.Series, dict[str, float]]:
    """Task 4: Compare high-value and low-value segment distributions and metrics."""
    q25 = revenue.quantile(0.25)
    q75 = revenue.quantile(0.75)

    # Include boundary values to avoid empty segments on small/tied datasets.
    high_value = revenue[revenue >= q75]
    low_value = revenue[revenue <= q25]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].hist(high_value, bins=30, alpha=0.7, label="High-Value")
    axes[0].hist(low_value, bins=30, alpha=0.7, label="Low-Value")
    axes[0].legend()
    axes[0].set_title("Revenue: High vs Low Value Customers")
    axes[0].set_xlabel("Revenue")
    axes[0].set_ylabel("Count")

    axes[1].boxplot([low_value, high_value], tick_labels=["Low-Value", "High-Value"])
    axes[1].set_title("Revenue Segment Spread (Boxplot)")
    axes[1].set_ylabel("Revenue")

    plt.tight_layout()
    plt.savefig(output_dir / "revenue_segments.png", dpi=150)
    plt.close(fig)

    segment_metrics = {
        "high_mean": float(high_value.mean()),
        "high_median": float(high_value.median()),
        "low_mean": float(low_value.mean()),
        "low_median": float(low_value.median()),
        "high_count": float(len(high_value)),
        "low_count": float(len(low_value)),
    }
    return high_value, low_value, segment_metrics


def build_business_interpretation(
    revenue: pd.Series,
    skewness: float,
    kurtosis: float,
    flags: dict[str, float],
) -> str:
    """Task 5: Convert statistical findings into business action guidance."""
    skew_label = "Highly right-skewed" if skewness > 1 else "Moderate"
    core_story = (
        "Most customers are small; a few large accounts pull up average revenue."
        if skewness > 1
        else "Revenue is more balanced across customers."
    )

    kurtosis_label = "Fat tails (outliers likely)" if kurtosis > 3 else "Near-normal tails"
    action = (
        "Segment lifecycle, pricing, and retention strategy separately for long-tail and enterprise-like customers."
        if skewness > 1
        else "A uniform strategy is reasonable with lighter segmentation."
    )

    hidden_segment_hint = (
        "Large jump from 75th to 90th percentile suggests a high-value sub-segment."
        if flags["gap_ratio_to_median"] > 0.5
        else "Upper-tail jump is limited; hidden high-value segment is less pronounced."
    )

    return f"""
Revenue Distribution Analysis
-----------------------------
Skewness: {skewness:.2f} -> {skew_label}
Mean: ${revenue.mean():.0f}
Median: ${revenue.median():.0f}
Interpretation: {core_story}

Kurtosis: {kurtosis:.2f} -> {kurtosis_label}
Max: ${revenue.max():.0f}
Top 1% threshold: ${revenue.quantile(0.99):.0f}
Top 1% revenue share: {flags['top_1pct_revenue_share']:.1%}

Hidden Segment Signal: {hidden_segment_hint}
Business Action: {action}
""".strip()


def run_analysis(input_path: Path | None, revenue_column: str | None, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    df = load_dataset(input_path)
    revenue, source_column = prepare_revenue_series(df, revenue_column)

    plot_distribution(revenue, output_dir)
    skewness, kurtosis = compute_moments(revenue)

    print(f"Using revenue source column: {source_column}")
    print(f"Rows analyzed: {len(revenue)}")

    print(f"Skewness: {skewness:.2f}")
    print(f"Kurtosis: {kurtosis:.2f}")
    if abs(skewness) > 1:
        print("Highly skewed - use median not mean")
    if kurtosis > 3:
        print("Heavy tails - expect outliers")

    print("\nRevenue describe():")
    print(revenue.describe())

    percentiles, flags = abnormal_pattern_report(revenue)
    print("\nSelected percentiles:")
    print(percentiles)
    print(f"\n0.75 to 0.90 gap: {flags['p75_p90_gap']:.2f}")
    print(f"Gap/median ratio: {flags['gap_ratio_to_median']:.2f}")
    print(f"Top 1% revenue share: {flags['top_1pct_revenue_share']:.1%}")

    _, _, segment_metrics = compare_segments(revenue, output_dir)
    print(
        "\nHigh-value: "
        f"mean={segment_metrics['high_mean']:.0f}, median={segment_metrics['high_median']:.0f}, "
        f"count={int(segment_metrics['high_count'])}"
    )
    print(
        "Low-value: "
        f"mean={segment_metrics['low_mean']:.0f}, median={segment_metrics['low_median']:.0f}, "
        f"count={int(segment_metrics['low_count'])}"
    )

    interpretation = build_business_interpretation(revenue, skewness, kurtosis, flags)
    print("\n" + interpretation)

    (output_dir / "revenue_distribution_interpretation.txt").write_text(interpretation + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze revenue distribution and hidden segments")
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Optional path to CSV containing a revenue-like column.",
    )
    parser.add_argument(
        "--revenue-column",
        type=str,
        default=None,
        help="Optional exact column to use as revenue (overrides auto-detection).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(OUTPUT_DIR),
        help="Directory where plots and interpretation output are saved.",
    )
    args = parser.parse_args()

    input_path = Path(args.input) if args.input else None
    output_dir = Path(args.output_dir)
    run_analysis(input_path=input_path, revenue_column=args.revenue_column, output_dir=output_dir)


if __name__ == "__main__":
    main()