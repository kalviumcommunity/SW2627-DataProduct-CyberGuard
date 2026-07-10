import json
import os
from datetime import datetime

import numpy as np
import pandas as pd


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SOURCE_ROW_COLUMN = '_source_row_index'


def _resolve_repo_path(*parts):
    return os.path.join(BASE_DIR, *parts)


def _prepare_dataframe(df):
    prepared = df.copy()
    if SOURCE_ROW_COLUMN not in prepared.columns:
        prepared[SOURCE_ROW_COLUMN] = np.arange(len(prepared))
    return prepared


def detect_exact_duplicates(df):
    """
    Find rows where all values are identical.
    
    Returns: Tuple of (count, duplicate_rows_dataframe)
    """
    exact_dups = df.duplicated().sum()
    dup_rows = df[df.duplicated(keep=False)].sort_values(by=df.columns.tolist())

    print("\nEXACT DUPLICATE DETECTION")
    print("=" * 60)
    print(f"Exact duplicates found: {exact_dups}")
    print(f"Total duplicate rows (including originals): {len(dup_rows)}")

    if len(dup_rows) > 0:
        print("\nSample duplicate rows:")
        print(dup_rows.head(10).to_string())

    return exact_dups, dup_rows


def detect_near_duplicates(df, key_columns):
    """
    Find rows with same key values but different other fields.
    
    Args:
        df: Input DataFrame
        key_columns: Columns defining uniqueness (e.g., ['customer_id', 'date'])
    
    Returns:
        DataFrame showing near-duplicates grouped by key
    """
    duplicate_keys = df[df.duplicated(subset=key_columns, keep=False)]

    print("\nNEAR-DUPLICATE DETECTION")
    print("=" * 60)
    print(f"Records with duplicate keys: {len(duplicate_keys)}")
    print(f"Unique key combinations with duplicates: {len(duplicate_keys.groupby(key_columns))}")

    if len(duplicate_keys) > 0:
        print("\nSample groups with duplicate keys:")
        for keys, group in list(duplicate_keys.groupby(key_columns))[:3]:
            print(f"\n  Key: {keys}")
            print(f"  Records in group: {len(group)}")
            print(group.to_string())

    return duplicate_keys


def remove_exact_duplicates(df, keep='first'):
    """
    Remove exact duplicates, choosing which record to keep.
    
    Args:
        df: Input DataFrame
        keep: 'first' (keep oldest), 'last' (keep newest), or False (remove all)
    
    Returns:
        Deduplicated DataFrame with row counts documented
    """
    rows_before = len(df)

    subset_columns = [column_name for column_name in df.columns if column_name != SOURCE_ROW_COLUMN]
    df_dedup = df.drop_duplicates(subset=subset_columns, keep=keep)

    rows_after = len(df_dedup)
    rows_removed = rows_before - rows_after
    removal_pct = (rows_removed / rows_before) * 100 if rows_before else 0

    print("\nEXACT DUPLICATE REMOVAL")
    print("=" * 60)
    print(f"Keep strategy: {keep}")
    print(f"Rows before: {rows_before:,}")
    print(f"Rows after:  {rows_after:,}")
    print(f"Rows removed: {rows_removed:,} ({removal_pct:.2f}%)")

    return df_dedup


def remove_near_duplicates(df, key_columns, keep_strategy='most_complete'):
    """
    Remove near-duplicates by choosing best record.
    
    Args:
        df: Input DataFrame
        key_columns: Columns defining uniqueness
        keep_strategy: 'most_complete' (fewest nulls), 'first', 'last'
    
    Returns:
        Deduplicated DataFrame
    """
    rows_before = len(df)

    if keep_strategy == 'most_complete':
        def keep_most_complete(group):
            null_counts = group.drop(columns=[SOURCE_ROW_COLUMN], errors='ignore').isnull().sum(axis=1)
            best_idx = null_counts.idxmin()
            return group.loc[[best_idx]]

        df_dedup = (
            df.groupby(key_columns, as_index=False, group_keys=False)
            .apply(keep_most_complete)
            .reset_index(drop=True)
        )
    elif keep_strategy == 'last':
        df_dedup = df.drop_duplicates(subset=key_columns, keep='last')
    else:
        df_dedup = df.drop_duplicates(subset=key_columns, keep='first')

    rows_after = len(df_dedup)
    rows_removed = rows_before - rows_after
    removal_pct = (rows_removed / rows_before) * 100 if rows_before else 0

    print("\nNEAR-DUPLICATE REMOVAL")
    print("=" * 60)
    print(f"Keep strategy: {keep_strategy}")
    print(f"Key columns: {key_columns}")
    print(f"Rows before: {rows_before:,}")
    print(f"Rows after:  {rows_after:,}")
    print(f"Rows removed: {rows_removed:,} ({removal_pct:.2f}%)")

    return df_dedup


def log_removed_duplicates(df_original, df_dedup):
    """
    Save all removed duplicate rows to audit file for compliance.
    
    Returns: Audit summary
    """
    if SOURCE_ROW_COLUMN in df_original.columns and SOURCE_ROW_COLUMN in df_dedup.columns:
        removed_mask = ~df_original[SOURCE_ROW_COLUMN].isin(df_dedup[SOURCE_ROW_COLUMN])
        removed_records = df_original[removed_mask]
    else:
        removed_records = df_original.loc[~df_original.index.isin(df_dedup.index)]

    print("\nAUDIT LOGGING")
    print("=" * 60)
    print(f"Total records removed: {len(removed_records)}")

    removed_audit_path = _resolve_repo_path('output', 'removed_duplicates_audit.csv')
    os.makedirs(os.path.dirname(removed_audit_path), exist_ok=True)
    removed_records.drop(columns=[SOURCE_ROW_COLUMN], errors='ignore').to_csv(removed_audit_path, index=False)
    print("✓ Removed records saved to audit file")

    audit_summary = {
        'removal_timestamp': datetime.now().isoformat(),
        'total_removed': int(len(removed_records)),
        'reason': 'Duplicate detection and deduplication',
        'audit_file': 'output/removed_duplicates_audit.csv',
        'audit_note': 'All removed records logged for compliance and recovery if needed',
    }

    audit_summary_path = _resolve_repo_path('output', 'dedup_audit_summary.json')
    with open(audit_summary_path, 'w', encoding='utf-8') as f:
        json.dump(audit_summary, f, indent=2, default=str)

    print("✓ Audit summary saved")
    print("=" * 60)

    return removed_records, audit_summary


def compare_before_after(df_original, df_dedup):
    """
    Log before/after metrics confirming deduplication worked.
    
    Returns: Comparison dictionary
    """
    original_clean = df_original.drop(columns=[SOURCE_ROW_COLUMN], errors='ignore')
    dedup_clean = df_dedup.drop(columns=[SOURCE_ROW_COLUMN], errors='ignore')
    removal_percentage = round(((len(df_original) - len(df_dedup)) / len(df_original)) * 100, 2) if len(df_original) else 0

    comparison = {
        'rows_before': len(df_original),
        'rows_after': len(df_dedup),
        'rows_removed': len(df_original) - len(df_dedup),
        'removal_percentage': removal_percentage,
        'columns': len(original_clean.columns),
        'nulls_before': int(original_clean.isnull().sum().sum()),
        'nulls_after': int(dedup_clean.isnull().sum().sum()),
        'timestamp': datetime.now().isoformat(),
    }

    print("\n" + "=" * 70)
    print("DEDUPLICATION FINAL SUMMARY")
    print("=" * 70)
    print(f"Rows before: {comparison['rows_before']:,}")
    print(f"Rows after:  {comparison['rows_after']:,}")
    print(f"Removed:     {comparison['rows_removed']:,} ({comparison['removal_percentage']}%)")
    print(f"\nNulls before: {comparison['nulls_before']:,}")
    print(f"Nulls after:  {comparison['nulls_after']:,}")
    print(f"Null change:  {comparison['nulls_before'] - comparison['nulls_after']:,}")
    print("=" * 70)

    summary_path = _resolve_repo_path('output', 'dedup_summary.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(comparison, f, indent=2)

    return comparison


if __name__ == "__main__":
    df = pd.read_csv(_resolve_repo_path('data', 'raw', 'data_with_dupes.csv'))

    print("\n" + "=" * 70)
    print("STARTING DEDUPLICATION WORKFLOW")
    print("=" * 70)
    print(f"Initial record count: {len(df):,}")

    df_original = _prepare_dataframe(df)

    print("\n[Step 1/4] Detecting exact duplicates...")
    exact_count, exact_rows = detect_exact_duplicates(df_original.drop(columns=[SOURCE_ROW_COLUMN], errors='ignore'))

    print("\n[Step 2/4] Detecting near-duplicates by key...")
    near_dups = detect_near_duplicates(df_original.drop(columns=[SOURCE_ROW_COLUMN], errors='ignore'), key_columns=['customer_id', 'transaction_date'])

    print("\n[Step 3/4] Removing exact duplicates (keeping first)...")
    df_dedup = remove_exact_duplicates(df_original, keep='first')

    print("\n[Step 4/4] Removing near-duplicates (keeping most complete)...")
    df_dedup = remove_near_duplicates(
        df_dedup,
        key_columns=['customer_id', 'transaction_date'],
        keep_strategy='most_complete',
    )

    print("\n[Audit] Logging removed records for compliance...")
    log_removed_duplicates(df_original, df_dedup)

    compare_before_after(df_original, df_dedup)

    processed_path = _resolve_repo_path('data', 'processed', 'deduplicated_data.csv')
    df_dedup.drop(columns=[SOURCE_ROW_COLUMN], errors='ignore').to_csv(processed_path, index=False)
    print("\n✓ Deduplicated data saved to data/processed/deduplicated_data.csv")