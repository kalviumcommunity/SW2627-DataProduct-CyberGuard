from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"


def ingest_csv(filepath, delimiter=',', encoding='utf-8', dtype_dict=None):
    """
    Load CSV file with explicit parameters documented.

    Args:
        filepath: Path to CSV file
        delimiter: Field delimiter (comma by default, but could be semicolon or tab)
        encoding: File encoding (UTF-8 standard, but may be latin-1 or cp1252)
        dtype_dict: Dictionary mapping column names to data types

    Returns:
        Pandas DataFrame with shape and column names confirmed
    """
    try:
        df = pd.read_csv(
            filepath,
            delimiter=delimiter,
            encoding=encoding,
            dtype=dtype_dict,
        )
        print(f"✓ CSV loaded: {filepath}")
        print(f"  Shape: {df.shape[0]} rows × {df.shape[1]} columns")
        print(f"  Columns: {list(df.columns)}")
        return df
    except FileNotFoundError:
        print(f"Error: File not found - {filepath}")
        raise
    except UnicodeDecodeError:
        print(f"Encoding error: Could not decode with {encoding}")
        print("Try: latin-1, iso-8859-1, or cp1252")
        raise


def ingest_json(filepath, is_nested=False):
    """
    Load JSON file, handling nested structures by flattening them.

    Args:
        filepath: Path to JSON file
        is_nested: If True, flatten nested JSON structures into columns

    Returns:
        Pandas DataFrame with nested structures expanded
    """
    try:
        df = pd.read_json(filepath)

        if is_nested:
            # Flatten nested JSON: {'customer': {'name': 'Alice'}} -> 'customer.name': 'Alice'
            df = pd.json_normalize(df.to_dict(orient="records"), sep=".")
            print("✓ Nested JSON flattened to tabular format")

        print(f"✓ JSON loaded: {filepath}")
        print(f"  Shape: {df.shape[0]} rows × {df.shape[1]} columns")
        return df
    except FileNotFoundError:
        print(f"Error: File not found - {filepath}")
        raise


def ingest_csv_with_fallback(filepath, delimiters=[','], fallback_encodings=None):
    """
    Load CSV with fallback encodings if initial attempt fails.

    Tries multiple encodings and delimiters in sequence.
    """
    if fallback_encodings is None:
        fallback_encodings = ["utf-8", "latin-1", "iso-8859-1", "cp1252"]

    for delimiter in delimiters:
        for encoding in fallback_encodings:
            try:
                df = pd.read_csv(filepath, delimiter=delimiter, encoding=encoding)
                print(f"✓ Successfully loaded with delimiter='{delimiter}', encoding='{encoding}'")
                return df
            except (UnicodeDecodeError, pd.errors.ParserError):
                continue

    raise ValueError(f"Could not load {filepath} with any encoding/delimiter combination")


def document_ingestion(df, source_file):
    """
    Print detailed ingestion report for audit trail.
    """
    print(f"\n{'=' * 60}")
    print(f"INGESTION REPORT: {source_file}")
    print(f"{'=' * 60}")
    print(f"Rows: {df.shape[0]}")
    print(f"Columns: {df.shape[1]}")
    print(f"\nColumn Names & Data Types:")
    print(df.dtypes)
    print(f"\nNull Values Per Column:")
    print(df.isnull().sum())
    print(f"\nFirst 3 Rows:")
    print(df.head(3).to_string())
    print(f"{'=' * 60}\n")
    return df


def _ensure_sample_files():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    _ensure_sample_files()

    print("Starting multi-format ingestion...\n")

    # Comma-delimited UTF-8 CSV matches the sample file format and needs no type overrides.
    csv_df = ingest_csv(
        RAW_DIR / "customers.csv",
        delimiter=',',
        encoding='utf-8'
    )
    document_ingestion(csv_df, "customers.csv")

    # Flat JSON example: simple top-level keys load directly without normalization.
    json_df = ingest_json(
        RAW_DIR / "transactions.json",
        is_nested=False
    )
    document_ingestion(json_df, "transactions.json")

    # Nested JSON example: nested objects are expanded into dotted column names.
    nested_json_df = ingest_json(
        RAW_DIR / "transactions_nested.json",
        is_nested=True
    )
    document_ingestion(nested_json_df, "transactions_nested.json")

    csv_df.to_csv(PROCESSED_DIR / "customers_ingested.csv", index=False)
    json_df.to_csv(PROCESSED_DIR / "transactions_ingested.csv", index=False)
    nested_json_df.to_csv(PROCESSED_DIR / "transactions_nested_ingested.csv", index=False)

    print("\n✓ All data ingested and saved to processed/")