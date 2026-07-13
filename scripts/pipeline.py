from __future__ import annotations

from pathlib import Path
import json

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
OUTPUT_DIR = BASE_DIR / "output"

DATE_FORMAT = "%Y-%m-%d"
EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
PHONE_PATTERN = r"^\d{10}$"
EXPECTED_COLUMNS = {
    "customer_id",
    "age",
    "price",
    "birth_date",
    "email",
    "phone",
    "start_date",
    "end_date",
    "campaign_start_date",
    "campaign_end_date",
}


def build_sample_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "customer_id": [101, 102, None, 104, 105, 106],
            "age": [29, 41, 152, 33, -2, 66],
            "price": [120.50, -15.00, 250.00, 0.00, 89.99, 45.00],
            "birth_date": ["1995-02-10", "2050-01-01", "1980-06-15", "1979-11-20", "1910-05-30", "2001-08-09"],
            "email": ["alice@example.com", "bob.example.com", "carol@example.org", None, "ella@sample", "frank@example.com"],
            "phone": ["1234567890", "12345", "0987654321", "1112223333", "phone12345", None],
            "start_date": ["2025-01-01", "2025-02-01", "2025-03-01", "2025-04-01", "2025-05-01", "2025-06-01"],
            "end_date": ["2025-01-31", "2025-01-15", "2025-03-20", "2025-03-15", "2025-06-10", "2025-05-20"],
            "campaign_start_date": ["2025-01-01", "2025-02-01", "2025-03-01", "2025-04-01", "2025-05-01", "2025-06-01"],
            "campaign_end_date": ["2025-01-31", "2025-01-15", "2025-02-20", "2025-03-15", "2025-04-30", "2025-05-20"],
        }
    )


def load_data() -> pd.DataFrame:
    candidate = RAW_DIR / "sample.csv"
    if candidate.exists():
        df = pd.read_csv(candidate)
        if EXPECTED_COLUMNS.issubset(df.columns):
            return df

    return build_sample_data()


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()

    for column in ["birth_date", "start_date", "end_date", "campaign_start_date", "campaign_end_date"]:
        if column in result.columns:
            result[column] = pd.to_datetime(result[column], format=DATE_FORMAT, errors="coerce")

    for column in ["age", "price", "customer_id"]:
        if column in result.columns:
            result[column] = pd.to_numeric(result[column], errors="coerce")

    return result


def rule_summary(rule_name: str, mask: pd.Series) -> dict:
    failed_mask = ~mask.fillna(False)
    return {
        "rule": rule_name,
        "passed_rows": int(mask.sum()),
        "failed_rows": int(failed_mask.sum()),
        "pass_rate": round(float(mask.mean()) if len(mask) else 0.0, 4),
    }


def validate_data(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    result = df.copy()
    report: dict[str, object] = {}

    result["valid_age"] = result["age"].between(0, 150, inclusive="both")
    result["valid_price"] = result["price"].ge(0)
    result["valid_birth_date"] = result["birth_date"].between(pd.Timestamp("1920-01-01"), pd.Timestamp.now())
    result["valid_customer_id"] = result["customer_id"].notna()
    result["valid_email_format"] = result["email"].str.contains(EMAIL_PATTERN, na=False, regex=True)
    result["valid_phone"] = result["phone"].astype("string").str.match(PHONE_PATTERN, na=False)
    result["valid_date_order"] = result["end_date"].ge(result["start_date"])
    result["valid_campaign_date_order"] = result["campaign_end_date"].ge(result["campaign_start_date"])

    report["valid_age"] = rule_summary("valid_age", result["valid_age"])
    report["valid_price"] = rule_summary("valid_price", result["valid_price"])
    report["valid_birth_date"] = rule_summary("valid_birth_date", result["valid_birth_date"])
    report["valid_customer_id"] = rule_summary("valid_customer_id", result["valid_customer_id"])
    report["valid_email_format"] = rule_summary("valid_email_format", result["valid_email_format"])
    report["valid_phone"] = rule_summary("valid_phone", result["valid_phone"])
    report["valid_date_order"] = rule_summary("valid_date_order", result["valid_date_order"])
    report["valid_campaign_date_order"] = rule_summary("valid_campaign_date_order", result["valid_campaign_date_order"])

    validation_columns = [
        "valid_age",
        "valid_price",
        "valid_birth_date",
        "valid_customer_id",
        "valid_email_format",
        "valid_phone",
        "valid_date_order",
        "valid_campaign_date_order",
    ]

    result["passes_all_checks"] = result[validation_columns].all(axis=1)
    report["validation_columns_used"] = validation_columns
    report["records_total"] = int(len(result))
    report["records_passed"] = int(result["passes_all_checks"].sum())
    report["records_failed"] = int((~result["passes_all_checks"]).sum())
    report["failed_record_ids"] = result.loc[~result["passes_all_checks"], "customer_id"].dropna().astype(int).tolist()

    return result, report


def write_validation_outputs(df: pd.DataFrame, report: dict) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    failures = df[~df["passes_all_checks"]].copy()
    failures.to_csv(OUTPUT_DIR / "validation_failures.csv", index=False)

    report_payload = {
        "summary": {
            "records_total": report["records_total"],
            "records_passed": report["records_passed"],
            "records_failed": report["records_failed"],
            "validation_columns_used": report["validation_columns_used"],
        },
        "rules": {
            key: value
            for key, value in report.items()
            if key not in {"records_total", "records_passed", "records_failed", "validation_columns_used", "failed_record_ids"}
        },
        "failed_record_ids": report["failed_record_ids"],
    }

    with open(OUTPUT_DIR / "validation_report.json", "w", encoding="utf-8") as handle:
        json.dump(report_payload, handle, indent=2, default=str)


def main() -> None:
    df = normalize_dataframe(load_data())
    validated_df, report = validate_data(df)
    write_validation_outputs(validated_df, report)

    print(f"Records: {report['records_total']}")
    print(f"Passed: {report['records_passed']}")
    print(f"Failed: {report['records_failed']}")
    print(f"Failures saved to: {OUTPUT_DIR / 'validation_failures.csv'}")
    print(f"Validation report saved to: {OUTPUT_DIR / 'validation_report.json'}")
    print(f"Clean records ready for analysis: {int(validated_df['passes_all_checks'].sum())}")


if __name__ == "__main__":
    main()