import argparse
import json
import os
from typing import Dict, List, Tuple

import pandas as pd


DATA_DICTIONARY = {
    "transaction_id": {
        "type": "integer",
        "format": None,
        "business_context": "Unique transaction identifier for traceability and joins.",
    },
    "customer_id": {
        "type": "integer",
        "format": None,
        "business_context": "Customer key used to relate transactions to customer records.",
    },
    "transaction_date": {
        "type": "datetime",
        "format": "%Y-%m-%d",
        "business_context": "Transaction timestamp used for chronological analysis and time windows.",
    },
    "customer_name": {
        "type": "string",
        "format": None,
        "business_context": "Customer display name used in reports and grouping.",
    },
    "transaction_amount": {
        "type": "currency",
        "format": "strip $ and commas, then convert to float",
        "business_context": "Monetary value used for revenue-style calculations.",
    },
    "signup_date": {
        "type": "datetime",
        "format": "%Y-%m-%d",
        "business_context": "Customer registration date used for cohort and lifecycle analysis.",
    },
    "amount": {
        "type": "currency",
        "format": "strip $ and commas, then convert to float",
        "business_context": "Monetary value used for revenue, spend, and fraud-related calculations.",
    },
    "is_active": {
        "type": "boolean",
        "format": "0/1, true/false, yes/no",
        "business_context": "Operational flag indicating whether a customer or record is active.",
    },
    "status": {
        "type": "string",
        "format": None,
        "business_context": "Business state of the transaction such as completed or pending.",
    },
    "name": {
        "type": "string",
        "format": None,
        "business_context": "Customer display name used for reporting and reference.",
    },
    "email": {
        "type": "string",
        "format": None,
        "business_context": "Customer contact email used for identity and communication.",
    },
}

TYPE_SCHEMAS = {
    "sample": {
        "customer_id": "integer",
        "customer_name": "string",
        "transaction_amount": "currency",
        "transaction_date": "datetime",
    },
    "enforcement_test": {
        "transaction_id": "integer",
        "customer_id": "integer",
        "transaction_date": "datetime",
        "amount": "currency",
        "is_active": "boolean",
        "status": "string",
    },
    "customers": {
        "customer_id": "integer",
        "name": "string",
        "email": "string",
        "signup_date": "datetime",
    },
    "transactions": {
        "id": "integer",
        "customer_id": "integer",
        "amount": "integer",
        "status": "string",
    },
}


def _normalise_series(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip()


def enforce_datetime(series: pd.Series, date_format: str, column_name: str) -> pd.Series:
    """Convert a string column to datetime using an explicit format."""
    try:
        return pd.to_datetime(series, format=date_format, errors="raise")
    except Exception as exc:
        invalid_mask = pd.to_datetime(series, format=date_format, errors="coerce").isna() & series.notna()
        invalid_values = series[invalid_mask].astype(str).head(5).tolist()
        raise ValueError(
            f"Failed to convert column '{column_name}' to datetime using format '{date_format}'. "
            f"Invalid values: {invalid_values}"
        ) from exc


def enforce_currency(series: pd.Series, column_name: str) -> pd.Series:
    """Strip currency symbols and convert to float."""
    cleaned = _normalise_series(series).str.replace(r"[$,]", "", regex=True)
    numeric = pd.to_numeric(cleaned, errors="coerce")
    invalid_mask = numeric.isna() & cleaned.notna() & (cleaned != "")

    if invalid_mask.any():
        invalid_values = cleaned[invalid_mask].head(5).tolist()
        raise ValueError(
            f"Failed to convert column '{column_name}' to numeric currency values. Invalid values: {invalid_values}"
        )

    return numeric.astype(float)


def enforce_boolean(series: pd.Series, column_name: str) -> pd.Series:
    """Convert boolean-like values to actual booleans."""
    mapping = {
        1: True,
        0: False,
        "1": True,
        "0": False,
        True: True,
        False: False,
        "true": True,
        "false": False,
        "yes": True,
        "no": False,
        "y": True,
        "n": False,
        "t": True,
        "f": False,
    }

    normalised = _normalise_series(series).str.lower()
    converted = normalised.map(mapping)
    invalid_mask = converted.isna() & normalised.notna() & (normalised != "")

    if invalid_mask.any():
        invalid_values = normalised[invalid_mask].head(5).tolist()
        raise ValueError(
            f"Failed to convert column '{column_name}' to boolean. Invalid values: {invalid_values}"
        )

    return converted.astype("boolean")


def enforce_integer(series: pd.Series, column_name: str) -> pd.Series:
    """Convert values to nullable integers."""
    numeric = pd.to_numeric(series, errors="coerce")
    invalid_mask = numeric.isna() & series.notna()

    if invalid_mask.any():
        invalid_values = series[invalid_mask].astype(str).head(5).tolist()
        raise ValueError(
            f"Failed to convert column '{column_name}' to integer. Invalid values: {invalid_values}"
        )

    return numeric.astype("Int64")


def enforce_string(series: pd.Series) -> pd.Series:
    return series.astype("string")


def enforce_column_types(df: pd.DataFrame, schema: Dict[str, str]) -> Tuple[pd.DataFrame, List[Dict[str, str]]]:
    """Apply explicit type enforcement and capture a conversion log."""
    converted_df = df.copy()
    conversion_log = []

    for column_name, target_type in schema.items():
        if column_name not in converted_df.columns:
            raise KeyError(f"Missing required column '{column_name}' for type enforcement.")

        before_dtype = str(converted_df[column_name].dtype)

        if target_type == "datetime":
            date_format = DATA_DICTIONARY.get(column_name, {}).get("format", "%Y-%m-%d") or "%Y-%m-%d"
            converted_df[column_name] = enforce_datetime(converted_df[column_name], date_format, column_name)
        elif target_type == "currency":
            converted_df[column_name] = enforce_currency(converted_df[column_name], column_name)
        elif target_type == "boolean":
            converted_df[column_name] = enforce_boolean(converted_df[column_name], column_name)
        elif target_type == "integer":
            converted_df[column_name] = enforce_integer(converted_df[column_name], column_name)
        else:
            converted_df[column_name] = enforce_string(converted_df[column_name])

        after_dtype = str(converted_df[column_name].dtype)
        conversion_log.append(
            {
                "column": column_name,
                "target_type": target_type,
                "before_dtype": before_dtype,
                "after_dtype": after_dtype,
            }
        )

    return converted_df, conversion_log


def compare_dtypes(before_df: pd.DataFrame, after_df: pd.DataFrame) -> List[Dict[str, str]]:
    """Build a before/after dtype comparison report."""
    comparisons = []
    for column_name in before_df.columns:
        if column_name not in after_df.columns:
            continue
        comparisons.append(
            {
                "column": column_name,
                "before_dtype": str(before_df[column_name].dtype),
                "after_dtype": str(after_df[column_name].dtype),
            }
        )
    return comparisons


def generate_type_report(df: pd.DataFrame, filepath: str, schema_name: str, output_path: str) -> Dict[str, object]:
    """Generate a structured type-enforcement report."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    schema = TYPE_SCHEMAS[schema_name]
    before_dtypes = df.dtypes.astype(str).to_dict()
    converted_df, conversion_log = enforce_column_types(df, schema)
    after_dtypes = converted_df.dtypes.astype(str).to_dict()

    report = {
        "dataset": filepath,
        "schema_name": schema_name,
        "record_count": len(df),
        "column_count": len(df.columns),
        "data_dictionary": {column: DATA_DICTIONARY.get(column, {}) for column in schema.keys()},
        "before_dtypes": before_dtypes,
        "after_dtypes": after_dtypes,
        "dtype_comparison": compare_dtypes(df, converted_df),
        "conversion_log": conversion_log,
    }

    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, default=str)

    processed_output = os.path.join("data", "processed", f"{os.path.splitext(os.path.basename(filepath))[0]}_typed.csv")
    os.makedirs(os.path.dirname(processed_output), exist_ok=True)
    converted_df.to_csv(processed_output, index=False)

    print(f"\n{'=' * 60}")
    print(f"TYPE ENFORCEMENT REPORT: {filepath}")
    print(f"{'=' * 60}")
    print(f"Records: {report['record_count']}")
    print(f"Columns: {report['column_count']}")
    print(f"Processed file: {processed_output}")
    print("\nBefore -> After dtypes:")
    for item in report["dtype_comparison"]:
        print(f"  {item['column']}: {item['before_dtype']} -> {item['after_dtype']}")
    print(f"{'=' * 60}\n")

    return report


def load_dataset(filepath: str) -> pd.DataFrame:
    extension = os.path.splitext(filepath)[1].lower()
    if extension == ".csv":
        return pd.read_csv(filepath)
    raise ValueError(f"Unsupported file type for type enforcement: {extension}")


def resolve_schema_name(filepath: str) -> str:
    filename = os.path.basename(filepath).lower()
    if "type_test" in filename or "enforcement_test" in filename:
        return "enforcement_test"
    if "sample" in filename:
        return "sample"
    if "customer" in filename:
        return "customers"
    if "transaction" in filename:
        return "transactions"
    return "sample"


def main() -> None:
    parser = argparse.ArgumentParser(description="Enforce explicit data types for CyberGuard datasets")
    parser.add_argument(
        "--input",
        default="data/raw/type_test.csv",
        help="Path to the raw CSV file to enforce types on",
    )
    parser.add_argument(
        "--output",
        default="output/type_enforcement_report.json",
        help="Path to save the JSON type enforcement report",
    )
    parser.add_argument(
        "--schema",
        default=None,
        help="Optional schema name. If omitted, one is inferred from the file name.",
    )
    args = parser.parse_args()

    schema_name = args.schema or resolve_schema_name(args.input)
    df = load_dataset(args.input)
    generate_type_report(df, args.input, schema_name, args.output)


if __name__ == "__main__":
    main()