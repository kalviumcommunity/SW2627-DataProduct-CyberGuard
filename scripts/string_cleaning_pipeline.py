from __future__ import annotations

import pandas as pd

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 140)
pd.set_option("display.max_colwidth", None)


SEGMENT_MAP = {
    "b2b": "B2B",
    "b 2 b": "B2B",
    "business-to-business": "B2B",
    "smb": "SMB",
    "small medium enterprise": "SMB",
    "small business": "SMB",
    "enterprise": "Enterprise",
    "ent": "Enterprise",
    "corporate": "Enterprise",
}

PRODUCT_MAP = {
    "electronics": "Electronics",
    "consumer electronics": "Electronics",
    "home electronics": "Electronics",
    "software": "Software",
    "saas": "Software",
    "subscription software": "Software",
    "services": "Services",
    "managed services": "Services",
    "professional services": "Services",
}

TIER_MAP = {
    "gold": "Gold",
    "gold tier": "Gold",
    "premium": "Gold",
    "silver": "Silver",
    "standard": "Silver",
    "bronze": "Bronze",
    "basic": "Bronze",
    "starter": "Bronze",
    "entry": "Bronze",
}

BUSINESS_DECISIONS = {
    "B2B": "Using B2B keeps the label aligned with CRM and sales reporting conventions.",
    "SMB": "Using SMB keeps the customer segment short and consistent across dashboards.",
    "Enterprise": "Using Enterprise preserves the business meaning while avoiding mixed casing.",
    "Electronics": "Using Electronics matches the merchandising taxonomy used in reporting.",
    "Software": "Using Software keeps product grouping broad enough for rollups.",
    "Services": "Using Services keeps operational services separate from products.",
    "Gold": "Using Gold keeps premium tiers easy to sort and explain to stakeholders.",
    "Silver": "Using Silver matches the mid-tier customer package naming.",
    "Bronze": "Using Bronze keeps entry-level plans grouped under a single canonical label.",
}


def create_sample_data() -> pd.DataFrame:
    """Create a small dataset with intentionally messy text fields."""
    return pd.DataFrame(
        {
            "customer_name": [" John ", "john", "JOHN", "John", "  JANE  ", "María", None, ""],
            "product_name": [
                " Electronics ",
                "electronics",
                "ELECTRONICS",
                "Consumer Electronics",
                " software ",
                "SOFTWARE",
                "Managed Services",
                "services",
            ],
            "segment": [
                "B2B",
                "b2b",
                "B 2 B",
                "business-to-business",
                "SMB",
                "small medium enterprise",
                "Enterprise",
                "corporate",
            ],
            "location": [
                " São Paulo ",
                "Montréal",
                "Zürich",
                "New York",
                "  São Paulo",
                "München",
                "Bogotá",
                None,
            ],
            "service_tier": [" Gold ", "gold tier", "PREMIUM", "silver", "STANDARD", "bronze", "starter", "entry"],
        }
    )


def print_value_counts(df: pd.DataFrame, column: str, title: str) -> None:
    print(f"\n{title}")
    print(df[column].value_counts(dropna=False).to_string())


def print_head_comparison(before: pd.Series, after: pd.Series, label: str) -> None:
    comparison = pd.DataFrame({f"before_{label}": before.head(5), f"after_{label}": after.head(5)})
    print(f"\n{label} sample before/after")
    print(comparison.to_string(index=False))


def clean_text_column(
    series: pd.Series,
    lowercase: bool = True,
    strip: bool = True,
    remove_special: bool = False,
    mapping: dict | None = None,
) -> pd.Series:
    """Reusable text cleaning function for any string column."""
    result = series.copy()

    null_count = int(result.isna().sum())
    if null_count:
        print(f"Warning: {null_count} null values in column")

    if strip:
        result = result.str.strip()

    if lowercase:
        result = result.str.lower()

    if remove_special:
        result = result.str.replace(r"[^a-zA-Z0-9 ]", "", regex=True)

    if mapping:
        result = result.replace(mapping)

    return result


def strip_all_strings(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Strip whitespace from all string columns."""
    cleaned = df.copy()
    string_cols = cleaned.select_dtypes(include=["object", "string"]).columns
    report: dict[str, dict[str, int]] = {}
    total_whitespace_values = 0

    for col in string_cols:
        before = cleaned[col].copy()
        whitespace_mask = before.astype("string").str.contains(r"^\s|\s$", regex=True, na=False)
        whitespace_count = int(whitespace_mask.sum())
        before_unique = int(before.nunique(dropna=True))
        cleaned[col] = clean_text_column(before, lowercase=False, strip=True)
        after_unique = int(cleaned[col].nunique(dropna=True))
        total_whitespace_values += whitespace_count

        report[col] = {
            "whitespace_values": whitespace_count,
            "unique_before": before_unique,
            "unique_after": after_unique,
        }

        print(f"{col}: {before_unique} -> {after_unique} unique values; whitespace values fixed: {whitespace_count}")

    print(f"\nTotal whitespace issues fixed: {total_whitespace_values}")
    return cleaned, report


def normalize_casing(df: pd.DataFrame, columns_to_lower: list[str]) -> pd.DataFrame:
    """Normalize casing for specified columns."""
    cleaned = df.copy()
    for col in columns_to_lower:
        cleaned[col] = clean_text_column(cleaned[col], lowercase=True, strip=False)
        print(f"Normalized {col} to lowercase")
    return cleaned


def remove_special_characters(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Remove special characters from specified columns."""
    cleaned = df.copy()
    for col in columns:
        cleaned[col] = clean_text_column(cleaned[col], lowercase=False, strip=False, remove_special=True)
        print(f"Removed special characters from {col} using pattern [^a-zA-Z0-9 ]")
    return cleaned


def apply_label_mappings(df: pd.DataFrame, mapping_spec: dict[str, dict[str, str]]) -> pd.DataFrame:
    """Apply canonical label mappings to selected columns."""
    cleaned = df.copy()
    for col, mapping in mapping_spec.items():
        cleaned[col] = clean_text_column(cleaned[col], lowercase=True, strip=True, mapping=mapping)
        print(f"Mapped labels for {col}")
    return cleaned


def print_mapping_summary(before_df: pd.DataFrame, after_df: pd.DataFrame, columns: list[str]) -> None:
    for col in columns:
        print_value_counts(before_df, col, f"{col} before mapping")
        print_value_counts(after_df, col, f"{col} after mapping")


def print_business_decisions() -> None:
    print("\nBusiness decisions for canonical labels")
    for label, decision in BUSINESS_DECISIONS.items():
        print(f"- {label}: {decision}")


def run_edge_case_test() -> pd.Series:
    test_cases = ["  Product A  ", "PRODUCT B", "Product_C", None, ""]
    test_series = pd.Series(test_cases)
    result = clean_text_column(test_series, lowercase=True, strip=True, remove_special=True)
    print("\nEdge case test output")
    print(result.to_string(index=False))
    return result


def main() -> None:
    raw_df = create_sample_data()

    print("Raw dataset")
    print(raw_df.to_string(index=False))

    print_value_counts(raw_df, "customer_name", "Customer name before stripping")
    print_value_counts(raw_df, "product_name", "Product name before stripping")

    stripped_df, strip_report = strip_all_strings(raw_df)
    print_value_counts(stripped_df, "customer_name", "Customer name after stripping")
    print_value_counts(stripped_df, "product_name", "Product name after stripping")
    print_head_comparison(raw_df["customer_name"], stripped_df["customer_name"], "customer_name")

    lowered_df = normalize_casing(stripped_df, ["customer_name", "product_name", "segment"])
    print_head_comparison(stripped_df["customer_name"], lowered_df["customer_name"], "customer_name lowercased")
    print("\nJOHN / john / John collapse to:")
    print(lowered_df["customer_name"].value_counts(dropna=False).to_string())

    special_clean_df = remove_special_characters(lowered_df, ["location"])
    print_head_comparison(lowered_df["location"], special_clean_df["location"], "location special-char clean")
    print("\nRegex explanation: [^a-zA-Z0-9 ] removes any character that is not a letter, digit, or space.")

    mapped_df = apply_label_mappings(
        special_clean_df,
        {
            "segment": SEGMENT_MAP,
            "product_name": PRODUCT_MAP,
            "service_tier": TIER_MAP,
        },
    )

    print_mapping_summary(lowered_df, mapped_df, ["segment", "product_name", "service_tier"])
    print_business_decisions()

    print("\nColumns cleaned and whitespace summary")
    for column, details in strip_report.items():
        print(
            f"- {column}: whitespace values={details['whitespace_values']}, "
            f"unique_before={details['unique_before']}, unique_after={details['unique_after']}"
        )

    print("\nFinal cleaned dataset")
    print(mapped_df.to_string(index=False))

    run_edge_case_test()


if __name__ == "__main__":
    main()
