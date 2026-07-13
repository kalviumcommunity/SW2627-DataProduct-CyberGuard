from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
OUTPUT_DIR = BASE_DIR / "output"

REVENUE_COLUMN = "revenue"
AGE_COLUMN = "age"
Z_SCORE_THRESHOLD = 3.0
IQR_MULTIPLIER = 1.5

def build_sample_data() -> pd.DataFrame:
    """Create a small customer revenue dataset with intentional outliers."""
    return pd.DataFrame(
        {
            "customer_id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "customer_name": [
                "Alice",
                "Bob",
                "Carol",
                "David",
                "Ella",
                "Frank",
                "Grace",
                "Henry",
                "Ivy",
                "Jack",
            ],
            "revenue": [120.0, 135.0, 128.0, 142.0, 150.0, 165.0, 175.0, 180.0, 500.0, 155.0],
            "age": [24, 31, 29, 43, 52, 38, 28, 41, 150, 36],
        }
    )

def load_data(input_path: Path | None = None) -> pd.DataFrame:
    """Load a customer dataset or fall back to a built-in sample."""
    if input_path and input_path.exists():
        return pd.read_csv(input_path)

    fallback_candidates = [
        RAW_DIR / "customer_revenue.csv",
        RAW_DIR / "revenue_customers.csv",
        RAW_DIR / "sample.csv",
    ]

    for candidate in fallback_candidates:
        if candidate.exists():
            df = pd.read_csv(candidate)
            if REVENUE_COLUMN in df.columns and AGE_COLUMN in df.columns:
                return df

    return build_sample_data()

def ensure_numeric(series: pd.Series) -> pd.Series:
    """Convert a column to numeric values safely."""
    return pd.to_numeric(series, errors="coerce")

def detect_zscore_outliers(df: pd.DataFrame, column: str, threshold: float = Z_SCORE_THRESHOLD) -> pd.DataFrame:
    """Add an absolute z-score column and a boolean outlier flag."""
    result = df.copy()
    values = result[column].astype(float)
    zscores = stats.zscore(values, nan_policy="omit")
    result[f"{column}_zscore"] = np.abs(zscores)
    result[f"is_{column}_outlier_zscore"] = result[f"{column}_zscore"] > threshold
    return result

def detect_iqr_outliers(df: pd.DataFrame, column: str, multiplier: float = IQR_MULTIPLIER) -> tuple[pd.DataFrame, float, float]:
    """Add IQR-based outlier flags and return the lower and upper thresholds."""
    result = df.copy()
    q1 = result[column].quantile(0.25)
    q3 = result[column].quantile(0.75)
    iqr = q3 - q1
    lower = q1 - multiplier * iqr
    upper = q3 + multiplier * iqr
    result[f"is_{column}_outlier_iqr"] = (result[column] < lower) | (result[column] > upper)
    return result, lower, upper

def cap_revenue_outliers(df: pd.DataFrame, lower: float, upper: float) -> pd.DataFrame:
    """Cap revenue outliers at the IQR boundaries."""
    result = df.copy()
    result["revenue_capped"] = result[REVENUE_COLUMN].clip(lower=lower, upper=upper)
    result["revenue_final"] = result["revenue_capped"]
    return result

def handle_age_outliers(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, float, float]:
    """Flag impossible ages and remove them from the cleaned dataset."""
    result = df.copy()
    q1 = result[AGE_COLUMN].quantile(0.25)
    q3 = result[AGE_COLUMN].quantile(0.75)
    iqr = q3 - q1
    lower = q1 - IQR_MULTIPLIER * iqr
    upper = q3 + IQR_MULTIPLIER * iqr

    result["age_zscore"] = np.abs(stats.zscore(result[AGE_COLUMN].astype(float), nan_policy="omit"))
    result["is_age_outlier_iqr"] = (result[AGE_COLUMN] < lower) | (result[AGE_COLUMN] > upper)
    result["is_age_impossible"] = (result[AGE_COLUMN] < 0) | (result[AGE_COLUMN] > 120)
    result["is_age_outlier"] = result["is_age_outlier_iqr"] | result["is_age_impossible"]

    cleaned = result[~result["is_age_impossible"]].copy()
    return result, cleaned, lower, upper

def build_cleaning_log(
    revenue_lower: float,
    revenue_upper: float,
    revenue_outlier_count: int,
    age_lower: float,
    age_upper: float,
    age_outlier_count: int,
    age_removed_count: int,
) -> pd.DataFrame:
    """Create a cleaning log documenting all outlier decisions."""
    log_entries = [
        {
            "column": REVENUE_COLUMN,
            "method": "Z-score + IQR",
            "action": "cap + flag",
            "threshold_lower": revenue_lower,
            "threshold_upper": revenue_upper,
            "affected_rows": revenue_outlier_count,
            "rows_removed": 0,
            "rows_capped": revenue_outlier_count,
            "date": pd.Timestamp.now(),
            "decision_reason": "Revenue outliers distort averages, so values are capped at the IQR boundaries and flagged for downstream analysis.",
        },
        {
            "column": AGE_COLUMN,
            "method": "IQR + domain rule",
            "action": "remove + flag",
            "threshold_lower": age_lower,
            "threshold_upper": age_upper,
            "affected_rows": age_outlier_count,
            "rows_removed": age_removed_count,
            "rows_capped": 0,
            "date": pd.Timestamp.now(),
            "decision_reason": "Impossible ages above 120 are removed because they violate domain expectations and break downstream assumptions.",
        },
    ]
    return pd.DataFrame(log_entries)

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    input_path = RAW_DIR / "customer_revenue.csv"
    df = load_data(input_path if input_path.exists() else None)

    if REVENUE_COLUMN not in df.columns or AGE_COLUMN not in df.columns:
        df = build_sample_data()

    df = df.copy()
    df[REVENUE_COLUMN] = ensure_numeric(df[REVENUE_COLUMN])
    df[AGE_COLUMN] = ensure_numeric(df[AGE_COLUMN])

    df = detect_zscore_outliers(df, REVENUE_COLUMN, threshold=Z_SCORE_THRESHOLD)
    df, revenue_lower, revenue_upper = detect_iqr_outliers(df, REVENUE_COLUMN, multiplier=IQR_MULTIPLIER)
    revenue_outlier_count = int(df[f"is_{REVENUE_COLUMN}_outlier_iqr"].sum())

    df = cap_revenue_outliers(df, revenue_lower, revenue_upper)

    print(f"Z-score outliers: {int(df[f'is_{REVENUE_COLUMN}_outlier_zscore'].sum())}")
    print(f"IQR outliers: {revenue_outlier_count}")
    print(f"Before revenue cap: min={df[REVENUE_COLUMN].min()}, max={df[REVENUE_COLUMN].max()}")
    print(
        f"After revenue cap: min={df['revenue_capped'].min()}, max={df['revenue_capped'].max()}"
    )

    age_full_df, cleaned_df, age_lower, age_upper = handle_age_outliers(df)
    age_outlier_count = int(age_full_df["is_age_outlier"].sum())
    age_removed_count = int((~age_full_df.index.isin(cleaned_df.index)).sum())

    age_full_df["is_outlier"] = age_full_df[f"is_{REVENUE_COLUMN}_outlier_iqr"] | age_full_df[f"is_{REVENUE_COLUMN}_outlier_zscore"] | age_full_df["is_age_outlier"]
    cleaned_df = age_full_df[~age_full_df["is_age_impossible"]].copy()

    normal = age_full_df[~age_full_df["is_outlier"]]
    anomalies = age_full_df[age_full_df["is_outlier"]]

    cleaning_log = build_cleaning_log(
        revenue_lower=revenue_lower,
        revenue_upper=revenue_upper,
        revenue_outlier_count=revenue_outlier_count,
        age_lower=age_lower,
        age_upper=age_upper,
        age_outlier_count=age_outlier_count,
        age_removed_count=age_removed_count,
    )

    print(f"Normal records: {len(normal)}")
    print(f"Anomalies: {len(anomalies)}")
    print(f"Age outliers: {age_outlier_count}")
    print(f"Age removals: {age_removed_count}")

    print("\nRevenue summary")
    print(df[REVENUE_COLUMN].describe())

    print("\nAge summary")
    print(cleaned_df[AGE_COLUMN].describe())

    cleaned_df.to_csv(OUTPUT_DIR / "cleaned_customer_revenue.csv", index=False)
    age_full_df.to_csv(OUTPUT_DIR / "outlier_flagged_customer_revenue.csv", index=False)
    cleaning_log.to_csv(OUTPUT_DIR / "cleaning_log.csv", index=False)

    print(f"\nCleaning log saved to {OUTPUT_DIR / 'cleaning_log.csv'}")
    print(f"Cleaned data saved to {OUTPUT_DIR / 'cleaned_customer_revenue.csv'}")

if __name__ == "__main__":
    main()
