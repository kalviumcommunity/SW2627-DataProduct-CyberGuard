import argparse
import hashlib
import json
import os

import numpy as np
import pandas as pd


def sanitize_for_json(obj):
    """
    Recursively sanitize objects to be JSON-serializable.
    Converts NaN, Inf, -Inf, and NaT/NA to None.
    Converts numpy and pandas scalars to Python native types.
    """
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(x) for x in obj]
    elif isinstance(obj, (float, np.floating)):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, (int, np.integer)):
        return int(obj)
    elif pd.isna(obj):  # Catches np.nan, None, pd.NA, pd.NaT
        return None
    return obj


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


def profile_categorical_columns(df, top_n=5, redact_columns=None):
    """
    Summarise categorical columns with value distributions.

    Returns: Dictionary with unique counts and top values
    """
    if redact_columns is None:
        redact_columns = []

    categorical_cols = df.select_dtypes(include=["object", "category", "string"]).columns

    profile = {}
    for col in categorical_cols:
        # Exclude nulls from top values to align with unique_count (nunique dropna=True by default)
        top_vals_series = df[col].value_counts(dropna=True).head(top_n)
        
        top_values = {}
        for val, count in top_vals_series.items():
            val_str = str(val)
            if col in redact_columns:
                # Mask email format specifically, hash others
                if "@" in val_str:
                    parts = val_str.split("@")
                    masked = parts[0][0] + "***@" + parts[1] if len(parts[0]) > 0 else "***"
                else:
                    masked = hashlib.sha256(val_str.encode("utf-8")).hexdigest()[:8]
                top_values[masked] = int(count)
            else:
                top_values[val_str] = int(count)

        profile[col] = {
            "unique_count": int(df[col].nunique()),
            "top_values": top_values,
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


def generate_profile_report(df, filepath, output_path="output/profile_report.json", redact_columns=None):
    """
    Generate complete data quality report and save to JSON.

    Returns: Complete profile report dictionary
    """
    dir_name = os.path.dirname(output_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    numerical_profile = profile_numerical_columns(df)
    report = {
        "dataset": filepath,
        "record_count": len(df),
        "column_count": len(df.columns),
        "nulls_and_duplicates": profile_nulls_and_duplicates(df),
        "numerical_stats": numerical_profile.to_dict(orient="index"),
        "categorical_stats": profile_categorical_columns(df, redact_columns=redact_columns),
        "quality_issues": identify_quality_issues(df),
    }

    # Sanitize NaN/Inf/numpy types for strict JSON compliance
    sanitized_report = sanitize_for_json(report)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sanitized_report, f, indent=2, allow_nan=False)

    print(f"\n{'='*60}")
    print(f"DATA QUALITY PROFILE: {filepath}")
    print(f"{'='*60}")
    print(f"Records: {sanitized_report['record_count']}")
    print(f"Columns: {sanitized_report['column_count']}")
    print(f"\nQuality Issues Found: {len(sanitized_report['quality_issues'])}")
    for issue in sanitized_report["quality_issues"]:
        print(f"  [{issue['severity']}] {issue['type']} in {issue['column']}")
        print(f"    Value: {issue['value']} -> {issue['recommendation']}")
    print(f"{'='*60}\n")

    return sanitized_report


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
    parser.add_argument(
        "--output",
        default="output/profile_report.json",
        help="Path to save the JSON profile report",
    )
    parser.add_argument(
        "--redact-columns",
        default="email",
        help="Comma-separated list of categorical columns to redact in the report",
    )
    args = parser.parse_args()

    redact_cols = [c.strip() for c in args.redact_columns.split(",")] if args.redact_columns else []

    df = load_dataset(args.input)
    generate_profile_report(df, args.input, args.output, redact_columns=redact_cols)


if __name__ == "__main__":
    main()