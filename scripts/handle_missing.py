import io
import json
import os
import sys

import numpy as np
import pandas as pd


if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def analyze_missing_values(df):
    """
    Compute null counts and percentages before treatment.

    Returns: DataFrame with analysis of missing data by column
    """
    total_rows = len(df)
    if total_rows == 0:
        null_counts = df.isnull().sum()
        null_percentages = pd.Series([0.0] * len(df.columns), index=df.columns)
    else:
        null_counts = df.isnull().sum()
        null_percentages = (null_counts / total_rows * 100).round(2)

    missing_analysis = pd.DataFrame({
        'column': df.columns,
        'null_count': null_counts.values,
        'null_percentage': null_percentages.values,
        'data_type': df.dtypes.values,
        'null_meaning': ''
    })

    print("=" * 70)
    print("BEFORE IMPUTATION - Missing Value Analysis")
    print("=" * 70)
    print(missing_analysis.to_string(index=False))
    print(f"\nTotal rows: {len(df)}")
    print(f"Total cells: {len(df) * len(df.columns)}")
    print(f"Missing cells: {df.isnull().sum().sum()}")
    print("=" * 70)

    return missing_analysis


def impute_mean_median(df, numerical_cols, strategy='median'):
    """Fill numerical nulls with mean or median."""
    df_imputed = df.copy()
    for col in numerical_cols:
        if col not in df_imputed.columns:
            continue
        null_count = df_imputed[col].isnull().sum()
        if null_count > 0:
            fill_value = df_imputed[col].median() if strategy == 'median' else df_imputed[col].mean()
            df_imputed[col] = df_imputed[col].fillna(fill_value)
            print(f"  ✓ {col}: filled {null_count} nulls with {strategy} ({fill_value:.2f})")
    return df_imputed


def impute_mode(df, categorical_cols):
    """Fill categorical nulls with mode (most common value)."""
    df_imputed = df.copy()
    for col in categorical_cols:
        if col not in df_imputed.columns:
            continue
        null_count = df_imputed[col].isnull().sum()
        if null_count > 0:
            mode_series = df_imputed[col].mode(dropna=True)
            if mode_series.empty:
                continue
            mode_val = mode_series.iloc[0]
            df_imputed[col] = df_imputed[col].fillna(mode_val)
            print(f"  ✓ {col}: filled {null_count} nulls with mode '{mode_val}'")
    return df_imputed


def impute_forward_fill(df, time_series_cols):
    """Fill with previous value (for time-series data)."""
    df_imputed = df.copy()
    for col in time_series_cols:
        if col not in df_imputed.columns:
            continue
        null_count = df_imputed[col].isnull().sum()
        if null_count > 0:
            df_imputed[col] = df_imputed[col].ffill()
            print(f"  ✓ {col}: forward-filled {null_count} nulls")
    return df_imputed


def drop_rows_with_nulls(df, critical_cols):
    """Drop rows where critical columns are null."""
    existing_cols = [col for col in critical_cols if col in df.columns]
    if not existing_cols:
        print("  ✓ No critical columns found in dataset; no rows dropped")
        return df.copy()

    rows_before = len(df)
    df_imputed = df.dropna(subset=existing_cols)
    rows_dropped = rows_before - len(df_imputed)
    print(f"  ✓ Dropped {rows_dropped} rows with null in: {existing_cols}")
    return df_imputed


def document_imputation_decisions(df_original, df_imputed):
    """Document all imputation decisions with business justification."""

    decisions = {}

    if 'amount' in df_original.columns:
        decisions['amount'] = {
            'column_type': 'numerical',
            'null_count_before': int(df_original['amount'].isnull().sum()),
            'strategy': 'median_imputation',
            'value_used': None if df_original['amount'].dropna().empty else float(df_original['amount'].median()),
            'business_reasoning': 'Median purchase amount is representative of typical transaction. Mean would be skewed by high-value outliers. Maintains distribution integrity.',
            'risk_assessment': 'Low - median is stable metric resistant to outliers'
        }

    if 'email' in df_original.columns:
        null_count = int(df_original['email'].isnull().sum())
        decisions['email'] = {
            'column_type': 'categorical_identifier',
            'null_count_before': null_count,
            'strategy': 'drop_rows',
            'rows_affected': null_count,
            'business_reasoning': 'Email is critical for customer contact and marketing campaigns. Rows without email cannot be used for outreach. Data is incomplete.',
            'risk_assessment': 'Low - only affects small percentage of data'
        }

    if 'status_date' in df_original.columns:
        decisions['status_date'] = {
            'column_type': 'datetime_series',
            'null_count_before': int(df_original['status_date'].isnull().sum()),
            'strategy': 'forward_fill',
            'interpretation': 'Assumes last known status date is still valid until changed',
            'business_reasoning': 'For time-series analysis, forward fill preserves temporal continuity. Status typically does not change frequently.',
            'risk_assessment': 'Medium - assumes no change between observations'
        }

    for col in df_imputed.columns:
        if col in decisions:
            continue
        null_count = int(df_original[col].isnull().sum()) if col in df_original.columns else 0
        if null_count > 0:
            if pd.api.types.is_numeric_dtype(df_original[col]):
                inferred_strategy = 'median_imputation'
            elif pd.api.types.is_datetime64_any_dtype(df_original[col]):
                inferred_strategy = 'forward_fill'
            else:
                inferred_strategy = 'mode_imputation'

            decisions[col] = {
                'column_type': str(df_original[col].dtype) if col in df_original.columns else 'unknown',
                'null_count_before': null_count,
                'strategy': inferred_strategy,
                'business_reasoning': 'Column-specific handling applied based on available data and workflow rules.',
                'risk_assessment': 'Varies by column'
            }

    os.makedirs('output', exist_ok=True)
    with open('output/imputation_decisions.json', 'w', encoding='utf-8') as f:
        json.dump(decisions, f, indent=2, default=str)

    return decisions


def validate_imputation(df_original, df_imputed):
    """Compare metrics before and after imputation."""

    print("\n" + "=" * 70)
    print("AFTER IMPUTATION - Validation Report")
    print("=" * 70)
    print(f"Total rows before: {len(df_original)}")
    print(f"Total rows after:  {len(df_imputed)}")
    print(f"Rows removed: {len(df_original) - len(df_imputed)}")
    print(f"\nTotal nulls before: {df_original.isnull().sum().sum()}")
    print(f"Total nulls after:  {df_imputed.isnull().sum().sum()}")

    missing_after = pd.DataFrame({
        'column': df_imputed.columns,
        'null_count_after': df_imputed.isnull().sum().values,
        'null_percentage_after': (df_imputed.isnull().sum() / len(df_imputed) * 100).round(2).values if len(df_imputed) > 0 else np.zeros(len(df_imputed))
    })

    print("\nNull values by column after imputation:")
    print(missing_after.to_string(index=False))
    print("=" * 70)

    return missing_after


def main():
    input_path = 'data/raw/missing_data.csv'
    output_path = 'data/processed/cleaned_data.csv'

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df_original = pd.read_csv(input_path)

    print("Step 1: Analyzing missing values...")
    analyze_missing_values(df_original)

    print("\nStep 2: Applying imputation strategies...")
    df_imputed = drop_rows_with_nulls(df_original, ['customer_id', 'email'])
    df_imputed = impute_mean_median(df_imputed, ['amount', 'quantity'], strategy='median')
    df_imputed = impute_mode(df_imputed, ['name', 'category', 'region'])
    df_imputed = impute_forward_fill(df_imputed, ['last_updated', 'status_date'])

    print("\nStep 3: Documenting imputation decisions...")
    document_imputation_decisions(df_original, df_imputed)

    print("\nStep 4: Validating imputation...")
    validate_imputation(df_original, df_imputed)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_imputed.to_csv(output_path, index=False)
    print(f"\n✓ Cleaned data saved to {output_path}")


if __name__ == '__main__':
    main()