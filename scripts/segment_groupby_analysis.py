"""Segment-level churn and revenue analysis using groupby and pivot tables.

Implements:
1) Single-level groupby with multiple aggregations
2) Multi-level groupby (customer_type, product) + unstack
3) Pivot table view
4) Ranking top/bottom performers by churn and revenue contribution
5) Actionable segment insights export
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
OUTPUT_DIR = BASE_DIR / "output"


def build_segment_sample(seed: int = 42) -> pd.DataFrame:
    """Create a synthetic customer dataset matching the assignment business story."""
    rng = np.random.default_rng(seed)

    n_total = 1000
    n_enterprise = int(n_total * 0.05)
    n_smb = int(n_total * 0.40)
    n_startup = n_total - n_enterprise - n_smb

    products = np.array(["Core", "Advanced", "Security"])

    # Target revenue mix: enterprise dominates total revenue despite small customer share.
    total_revenue_target = 1_000_000.0
    target_revenue = {
        "Enterprise": total_revenue_target * 0.70,
        "SMB": total_revenue_target * 0.20,
        "Startup": total_revenue_target * 0.10,
    }

    enterprise_rev_raw = rng.lognormal(mean=3.2, sigma=0.55, size=n_enterprise)
    smb_rev_raw = rng.lognormal(mean=2.0, sigma=0.50, size=n_smb)
    startup_rev_raw = rng.lognormal(mean=1.8, sigma=0.50, size=n_startup)

    enterprise_rev = enterprise_rev_raw * (target_revenue["Enterprise"] / enterprise_rev_raw.sum())
    smb_rev = smb_rev_raw * (target_revenue["SMB"] / smb_rev_raw.sum())
    startup_rev = startup_rev_raw * (target_revenue["Startup"] / startup_rev_raw.sum())

    def build_segment_block(
        start_id: int,
        n_rows: int,
        segment: str,
        churn_rate: float,
        revenue_values: np.ndarray,
        support_lambda: float,
    ) -> pd.DataFrame:
        churn_count = int(round(n_rows * churn_rate))
        churn = np.zeros(n_rows, dtype=int)
        if churn_count > 0:
            churn_idx = rng.choice(np.arange(n_rows), size=churn_count, replace=False)
            churn[churn_idx] = 1
        support_tickets = np.clip(rng.poisson(support_lambda, size=n_rows), 0, None)
        product = rng.choice(products, size=n_rows, p=[0.45, 0.30, 0.25])

        return pd.DataFrame(
            {
                "customer_id": np.arange(start_id, start_id + n_rows),
                "customer_type": segment,
                "product": product,
                "churn": churn,
                "revenue": np.round(revenue_values, 2),
                "support_tickets": support_tickets,
            }
        )

    df_enterprise = build_segment_block(1, n_enterprise, "Enterprise", 0.01, enterprise_rev, 0.8)
    df_smb = build_segment_block(1 + n_enterprise, n_smb, "SMB", 0.12, smb_rev, 2.6)
    df_startup = build_segment_block(1 + n_enterprise + n_smb, n_startup, "Startup", 0.08, startup_rev, 1.9)

    df = pd.concat([df_enterprise, df_smb, df_startup], ignore_index=True)
    return df


def load_data(input_path: Path | None) -> tuple[pd.DataFrame, str]:
    """Load user-provided data or fallback to sample segmentation dataset."""
    if input_path:
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        return pd.read_csv(input_path), str(input_path)

    candidate = RAW_DIR / "segment_data.csv"
    if candidate.exists():
        return pd.read_csv(candidate), str(candidate)

    return build_segment_sample(), "generated_sample"


def validate_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Validate required columns and coerce numeric fields."""
    required = {"customer_type", "product", "churn", "revenue", "customer_id", "support_tickets"}
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"Missing required columns: {sorted(missing)}")

    result = df.copy()
    result["churn"] = pd.to_numeric(result["churn"], errors="coerce")
    result["revenue"] = pd.to_numeric(result["revenue"], errors="coerce")
    result["support_tickets"] = pd.to_numeric(result["support_tickets"], errors="coerce")
    result = result.dropna(subset=["churn", "revenue", "support_tickets", "customer_type", "product", "customer_id"])
    return result


def task1_single_level_groupby(df: pd.DataFrame) -> pd.DataFrame:
    """Task 1: Single-level groupby with multiple aggregations."""
    segment_metrics = df.groupby("customer_type").agg(
        {
            "churn": "mean",
            "revenue": "sum",
            "customer_id": "count",
            "support_tickets": "mean",
        }
    )

    segment_metrics.columns = ["churn_rate", "total_revenue", "customer_count", "avg_support_tickets"]
    return segment_metrics


def task2_multi_level_groupby(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Task 2: Multi-level groupby and unstacked pivot-like view."""
    product_segment = df.groupby(["customer_type", "product"]).agg(
        {
            "revenue": "sum",
            "customer_id": "count",
        }
    )

    product_segment.columns = ["total_revenue", "customer_count"]
    product_segment_pivot = product_segment.unstack()
    return product_segment, product_segment_pivot


def task3_pivot_table(df: pd.DataFrame) -> pd.DataFrame:
    """Task 3: Two-dimensional pivot of total revenue by customer_type and product."""
    pivot = pd.pivot_table(
        df,
        values="revenue",
        index="customer_type",
        columns="product",
        aggfunc="sum",
    )
    return pivot


def task4_rank_segments(segment_metrics: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Task 4: Rank by churn and compute revenue contribution percentages."""
    segment_metrics = segment_metrics.copy()
    segment_metrics["churn_rank"] = segment_metrics["churn_rate"].rank(method="dense")
    worst_first = segment_metrics.sort_values("churn_rate", ascending=False)

    revenue_total = segment_metrics["total_revenue"].sum()
    segment_metrics["revenue_contribution"] = (segment_metrics["total_revenue"] / revenue_total) * 100
    return segment_metrics, worst_first


def task5_actionable_insights(segment_metrics: pd.DataFrame) -> pd.DataFrame:
    """Task 5: Build action-oriented segment recommendations and export."""
    insights = []

    for segment in segment_metrics.index:
        row = segment_metrics.loc[segment]
        action = ""
        if row["churn_rate"] > 0.10:
            action = "HIGH PRIORITY: Churn above 10%. Investigate pain points."
        elif row["churn_rate"] < 0.02:
            action = "Healthy. Maintain current service level."
        else:
            action = "Monitor. No immediate action needed."

        insights.append(
            {
                "segment": segment,
                "customer_count": int(row["customer_count"]),
                "churn_rate": f"{row['churn_rate']:.1%}",
                "total_revenue": f"${row['total_revenue']:.0f}",
                "revenue_contribution": f"{row['revenue_contribution']:.1f}%",
                "avg_support_tickets": round(float(row["avg_support_tickets"]), 2),
                "action": action,
            }
        )

    insights_df = pd.DataFrame(insights)
    return insights_df


def run_analysis(input_path: Path | None, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    df_raw, source = load_data(input_path)
    df = validate_columns(df_raw)

    overall_churn = df["churn"].mean()
    print(f"Data source: {source}")
    print(f"Rows analyzed: {len(df)}")
    print(f"Dataset-wide churn rate: {overall_churn:.2%}\n")

    segment_metrics = task1_single_level_groupby(df)
    print("Task 1 - Segment metrics")
    print(segment_metrics)

    product_segment, product_segment_pivot = task2_multi_level_groupby(df)
    print("\nTask 2 - Multi-level groupby")
    print(product_segment_pivot)

    pivot = task3_pivot_table(df)
    print("\nTask 3 - Revenue pivot")
    print(pivot)

    segment_metrics_ranked, worst_first = task4_rank_segments(segment_metrics)
    print("\nTask 4 - Worst churn first")
    print(worst_first)
    print("\nRevenue contribution vs churn")
    print(segment_metrics_ranked[["revenue_contribution", "churn_rate"]])

    insights_df = task5_actionable_insights(segment_metrics_ranked)
    print("\nTask 5 - Actionable insights")
    print(insights_df.to_string(index=False))

    segment_metrics_ranked.to_csv(output_dir / "segment_metrics.csv")
    product_segment.to_csv(output_dir / "product_segment_groupby.csv")
    product_segment_pivot.to_csv(output_dir / "product_segment_unstacked.csv")
    pivot.to_csv(output_dir / "segment_revenue_pivot.csv")
    worst_first.to_csv(output_dir / "segment_worst_first.csv")
    insights_df.to_csv(output_dir / "segment_insights.csv", index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Segment-level groupby and actionable insights analysis")
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Optional path to CSV with customer_type, product, churn, revenue, customer_id, support_tickets.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(OUTPUT_DIR),
        help="Directory for generated segment analysis outputs.",
    )
    args = parser.parse_args()

    input_path = Path(args.input) if args.input else None
    run_analysis(input_path=input_path, output_dir=Path(args.output_dir))


if __name__ == "__main__":
    main()