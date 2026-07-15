"""Correlation analysis for churn with Pearson/Spearman, heatmap, and feature selection.

Implements:
1) Pearson and Spearman correlation comparison for churn
2) Correlation heatmap visualization
3) Strong correlation pair detection
4) Business interpretation with causation caveats
5) Feature selection based on redundancy in highly correlated features
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
OUTPUT_DIR = BASE_DIR / "output"


def build_sample_churn_data(n: int = 300, seed: int = 42) -> pd.DataFrame:
    """Create a realistic churn sample when no churn dataset is present in the repo."""
    rng = np.random.default_rng(seed)

    customer_pain = rng.normal(0, 1, n)
    engagement = np.clip(65 - (customer_pain * 12) + rng.normal(0, 4, n), 0, 100)
    transactions_per_month = np.clip((engagement / 7) + rng.normal(0, 0.7, n), 0, None)
    support_tickets = np.clip(np.round(1.8 + (customer_pain * 1.6) + rng.normal(0, 1.0, n)), 0, None)
    tenure_months = np.clip(np.round(24 - (customer_pain * 4) + rng.normal(0, 5, n)), 1, None)
    monthly_spend = np.clip(30 + (transactions_per_month * 9) + rng.normal(0, 20, n), 5, None)

    churn_score = (
        (customer_pain * 1.5)
        + (support_tickets * 0.2)
        - (engagement * 0.03)
        - (tenure_months * 0.03)
        + rng.normal(0, 0.8, n)
    )
    churn = (churn_score > np.quantile(churn_score, 0.62)).astype(int)

    return pd.DataFrame(
        {
            "engagement": engagement,
            "transactions_per_month": transactions_per_month,
            "support_tickets": support_tickets,
            "tenure_months": tenure_months,
            "monthly_spend": monthly_spend,
            "churn": churn,
        }
    )


def load_data(input_path: Path | None) -> tuple[pd.DataFrame, str]:
    """Load input CSV or fallback to generated sample churn data."""
    if input_path:
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        return pd.read_csv(input_path), str(input_path)

    candidate = RAW_DIR / "churn_data.csv"
    if candidate.exists():
        return pd.read_csv(candidate), str(candidate)

    return build_sample_churn_data(), "generated_sample"


def ensure_numeric_target(df: pd.DataFrame, target_col: str) -> pd.DataFrame:
    """Convert churn-like target to numeric and keep only numeric columns for correlations."""
    result = df.copy()

    if target_col not in result.columns:
        raise KeyError(f"Missing target column: {target_col}")

    if result[target_col].dtype == bool:
        result[target_col] = result[target_col].astype(int)
    elif not pd.api.types.is_numeric_dtype(result[target_col]):
        mapping = {
            "yes": 1,
            "true": 1,
            "churned": 1,
            "1": 1,
            "no": 0,
            "false": 0,
            "active": 0,
            "0": 0,
        }
        mapped = result[target_col].astype(str).str.strip().str.lower().map(mapping)
        numeric_target = pd.to_numeric(result[target_col], errors="coerce")
        result[target_col] = mapped.fillna(numeric_target)

    numeric_df = result.select_dtypes(include=["number"]).copy()
    numeric_df = numeric_df.dropna(axis=0)

    if target_col not in numeric_df.columns:
        raise ValueError("Target column became non-numeric after conversion or has only missing values.")

    if numeric_df.shape[1] < 2:
        raise ValueError("Need at least two numeric columns (including target) for correlation analysis.")

    return numeric_df


def compute_correlation_matrices(df_num: pd.DataFrame, target_col: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Task 1: Pearson and Spearman correlation with target comparison table."""
    pearson_corr = df_num.corr(method="pearson")
    spearman_corr = df_num.corr(method="spearman")

    comparison = pd.DataFrame(
        {
            "pearson": pearson_corr[target_col],
            "spearman": spearman_corr[target_col],
        }
    )
    comparison["abs_diff"] = (comparison["pearson"] - comparison["spearman"]).abs()
    comparison = comparison.sort_values("abs_diff", ascending=False)

    return pearson_corr, spearman_corr, comparison


def save_heatmap(corr: pd.DataFrame, output_dir: Path) -> None:
    """Task 2: Save correlation heatmap."""
    fig, ax = plt.subplots(figsize=(12, 10))
    sns.heatmap(corr, annot=True, cmap="coolwarm", center=0, ax=ax, fmt=".2f")
    ax.set_title("Feature Correlation Matrix")
    plt.tight_layout()
    plt.savefig(output_dir / "correlation_heatmap.png", dpi=150)
    plt.close(fig)


def strong_correlation_pairs(corr: pd.DataFrame, threshold: float = 0.7, top_n: int = 10) -> pd.Series:
    """Task 3: Return strongly correlated non-self pairs without duplicates."""
    upper_mask = np.triu(np.ones(corr.shape), k=1).astype(bool)
    upper = corr.where(upper_mask)
    strong = upper.stack().sort_values(key=lambda s: s.abs(), ascending=False)
    strong = strong[strong.abs() > threshold].head(top_n)
    strong.index.names = ["feature_1", "feature_2"]
    return strong


def build_business_analysis(
    strong_pairs: pd.Series,
    pearson_corr: pd.DataFrame,
    target_col: str,
) -> dict[str, dict[str, object]]:
    """Task 4: Convert strong correlations into actionable but non-causal interpretations."""
    analysis: dict[str, dict[str, object]] = {}
    relation_key = f"connection_to_{target_col}"

    for (left, right), corr_value in strong_pairs.items():
        pair_name = f"{left} <-> {right}"
        relation_to_target = []

        for col in (left, right):
            if col != target_col and target_col in pearson_corr.columns:
                relation_to_target.append(f"{col}: r={pearson_corr.loc[col, target_col]:.2f} with {target_col}")

        analysis[pair_name] = {
            "correlation": round(float(corr_value), 3),
            "possible_directions": [
                f"{left} -> {right}",
                f"{right} -> {left}",
                "Unobserved confounder may drive both",
            ],
            "data_indicates": "Strong association, not proof of causation. Validate with temporal or experimental evidence.",
            relation_key: relation_to_target,
            "action": "Use as an early warning signal and prioritize root-cause analysis rather than treating the proxy metric directly.",
        }

    support_key = f"support_tickets <-> {target_col}"
    if {"support_tickets", target_col}.issubset(set(pearson_corr.columns)):
        st_corr = float(pearson_corr.loc["support_tickets", target_col])
        analysis[support_key] = {
            "correlation": round(st_corr, 3),
            "possible_directions": [
                f"support_tickets -> {target_col} (friction drives exits)",
                f"{target_col} intent -> support_tickets (frustrated users seek help before leaving)",
                f"customer_pain -> both (confounding cause for support_tickets and {target_col})",
            ],
            "data_indicates": "Tickets are likely a symptom of underlying pain, not necessarily the root cause.",
            "action": "Reduce recurring customer pain points and improve first-contact resolution quality.",
        }

    return analysis


def feature_selection_by_correlation(
    df_num: pd.DataFrame,
    corr: pd.DataFrame,
    target_col: str,
    threshold: float = 0.9,
) -> tuple[pd.DataFrame, list[str]]:
    """Task 5: Drop redundant features from highly correlated pairs and keep interpretable set."""
    selected_cols = [c for c in df_num.columns if c != target_col]
    dropped: list[str] = []

    for i, col_i in enumerate(selected_cols.copy()):
        for col_j in selected_cols[i + 1 :]:
            if col_i in dropped or col_j in dropped:
                continue

            pair_corr = corr.loc[col_i, col_j]
            if abs(pair_corr) >= threshold:
                keep = col_i
                drop = col_j

                if "transactions_per_month" in (col_i, col_j) and "engagement" in (col_i, col_j):
                    keep = "transactions_per_month"
                    drop = "engagement"
                else:
                    if len(col_j) < len(col_i):
                        keep, drop = col_j, col_i

                dropped.append(drop)

    final_cols = [c for c in selected_cols if c not in dropped] + [target_col]
    return df_num[final_cols].copy(), dropped


def run_analysis(input_path: Path | None, target_col: str, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    df, source = load_data(input_path)
    df_num = ensure_numeric_target(df, target_col)

    pearson_corr, spearman_corr, comparison = compute_correlation_matrices(df_num, target_col)
    print("Task 1 - Pearson vs Spearman comparison against target:")
    print(comparison)

    save_heatmap(pearson_corr, output_dir)
    print("\nTask 2 - Heatmap saved:")
    print(output_dir / "correlation_heatmap.png")

    strong_pairs = strong_correlation_pairs(pearson_corr, threshold=0.7, top_n=10)
    print("\nTask 3 - Strongly correlated pairs (|r| > 0.7):")
    print(strong_pairs)

    analysis = build_business_analysis(strong_pairs, pearson_corr, target_col)
    print("\nTask 4 - Business interpretation:")
    print(json.dumps(analysis, indent=2))

    df_features, dropped = feature_selection_by_correlation(df_num, pearson_corr, target_col, threshold=0.9)
    print("\nTask 5 - Feature selection by redundancy:")
    print(f"Dropped features: {dropped if dropped else 'None'}")
    print(df_features.corr())

    comparison.to_csv(output_dir / "pearson_spearman_comparison.csv")
    strong_pairs.rename("pearson_corr").to_csv(output_dir / "strong_correlation_pairs.csv")
    with open(output_dir / "correlation_business_interpretation.json", "w", encoding="utf-8") as handle:
        json.dump(analysis, handle, indent=2)
    df_features.corr().to_csv(output_dir / "selected_feature_correlation.csv")

    metadata = {
        "data_source": source,
        "rows_analyzed": int(df_num.shape[0]),
        "numeric_columns": df_num.columns.tolist(),
        "target_column": target_col,
        "dropped_redundant_features": dropped,
    }
    with open(output_dir / "correlation_analysis_metadata.json", "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Correlation analysis for churn business interpretation")
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Optional input CSV path. If omitted, script uses data/raw/churn_data.csv if present; otherwise a generated sample.",
    )
    parser.add_argument(
        "--target",
        type=str,
        default="churn",
        help="Target column for correlation comparison.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(OUTPUT_DIR),
        help="Directory to save correlation outputs.",
    )
    args = parser.parse_args()

    input_path = Path(args.input) if args.input else None
    run_analysis(input_path=input_path, target_col=args.target, output_dir=Path(args.output_dir))


if __name__ == "__main__":
    main()