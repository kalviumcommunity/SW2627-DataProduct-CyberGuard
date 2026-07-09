import argparse
import json
import os

import numpy as np
import pandas as pd


def profile_nulls_and_duplicates(df):
    """
    Compute null percentage and duplicate counts per column.

    Returns: Dictionary with null analysis by column
    """
    profile = {
        "null_counts": {},
        "null_percentages": {},
        "exact_duplicate_count": 0,
    }

    row_count = len(df)
    for col in df.columns:
        null_count = df[col].isna().sum()
        null_pct = (null_count / row_count) * 100 if row_count else 0
        profile["null_counts"][col] = int(null_count)
        profile["null_percentages"][col] = round(null_pct, 2)

    duplicate_count = int(df.duplicated().sum())
    duplicate_pct = (duplicate_count / row_count) * 100 if row_count else 0
    profile["exact_duplicate_count"] = duplicate_count
    profile["duplicate_percentage"] = round(duplicate_pct, 2)

    return profile


def profile_numerical_columns(df):
    """
    Summarise numerical columns with statistical measures.

    Returns: DataFrame with min, max, mean, median, std
    """
    numerical_cols = df.select_dtypes(include=[np.number]).columns

    stats = {}
    for col in numerical_cols:
        stats[col] = {
            "min": round(df[col].min(), 2),
            "max": round(df[col].max(), 2),
            "mean": round(df[col].mean(), 2),
            "median": round(df[col].median(), 2),
            "std": round(df[col].std(), 2),
            "null_count": int(df[col].isnull().sum()),
        }

    return pd.DataFrame(stats).T


def profile_categorical_columns(df, top_n=5):
    """
    Summarise categorical columns with value distributions.

    Returns: Dictionary with unique counts and top values
    """
    categorical_cols = df.select_dtypes(include=["object", "category", "string"]).columns

    profile = {}
    for col in categorical_cols:
        profile[col] = {
            "unique_count": int(df[col].nunique()),
            "top_values": df[col].value_counts(dropna=False).head(top_n).to_dict(),
            "null_count": int(df[col].isnull().sum()),
        }

    return profile


def identify_quality_issues(df, null_threshold=30, duplicate_threshold=5):
    """
    Identify data quality problems based on thresholds.

    Returns: List of issues found with severity and recommendations
    """
    issues = []

    if len(df) == 0:
        return issues

    # Check nulls
    null_pcts = (df.isnull().sum() / len(df)) * 100
    for col, pct in null_pcts.items():
        if pct > null_threshold:
            issues.append(
                {
                    "type": "High nulls",
                    "column": col,
                    "severity": "HIGH",
                    "value": f"{pct:.1f}% missing",
                    "recommendation": "Consider imputation or column exclusion",
                }
            )

    # Check duplicates
    dup_count = int(df.duplicated().sum())
    dup_pct = (dup_count / len(df)) * 100
    if dup_pct > duplicate_threshold:
        issues.append(
            {
                "type": "High duplicates",
                "column": "Full row",
                "severity": "HIGH",
                "value": f"{dup_pct:.1f}% duplicated",
                "recommendation": "Deduplication required before analysis",
            }
        )

    # Check for invalid ranges
    for col in df.select_dtypes(include=[np.number]).columns:
        if (df[col] < 0).any() and "amount" in col.lower():
            issues.append(
                {
                    "type": "Invalid range",
                    "column": col,
                    "severity": "MEDIUM",
                    "value": "Contains negative values",
                    "recommendation": "Investigate negative entries",
                }
            )

    return issues


def generate_profile_report(df, filepath):
    """
    Generate complete data quality report and save to JSON.

    Returns: Complete profile report dictionary
    """
    os.makedirs("output", exist_ok=True)

    numerical_profile = profile_numerical_columns(df)
    report = {
        "dataset": filepath,
        "record_count": len(df),
        "column_count": len(df.columns),
        "nulls_and_duplicates": profile_nulls_and_duplicates(df),
        "numerical_stats": numerical_profile.to_dict(orient="index"),
        "categorical_stats": profile_categorical_columns(df),
        "quality_issues": identify_quality_issues(df),
    }

    with open("output/profile_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n{'='*60}")
    print(f"DATA QUALITY PROFILE: {filepath}")
    print(f"{'='*60}")
    print(f"Records: {report['record_count']}")
    print(f"Columns: {report['column_count']}")
    print(f"\nQuality Issues Found: {len(report['quality_issues'])}")
    for issue in report["quality_issues"]:
        print(f"  [{issue['severity']}] {issue['type']} in {issue['column']}")
        print(f"    Value: {issue['value']} -> {issue['recommendation']}")
    print(f"{'='*60}\n")

    return report


def load_dataset(filepath):
    extension = os.path.splitext(filepath)[1].lower()
    if extension != ".csv":
        raise ValueError(f"Unsupported format for profiling: {extension}")
    return pd.read_csv(filepath)


def main():
    parser = argparse.ArgumentParser(description="Profile raw data quality for CyberGuard")
    parser.add_argument(
        "--input",
        default="data/raw/quality_test.csv",
        help="Path to the CSV file to profile",
    )
    args = parser.parse_args()

    df = load_dataset(args.input)
    generate_profile_report(df, args.input)


if __name__ == "__main__":
    main()