from __future__ import annotations

from pathlib import Path
import json

import pandas as pd


def _require_columns(df: pd.DataFrame, required_columns: set[str]) -> None:
    missing = sorted(required_columns - set(df.columns))
    if missing:
        raise KeyError(f"Missing required columns: {missing}")


def _normalize_transactions(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    if "transaction_date" in result.columns:
        result["transaction_date"] = pd.to_datetime(result["transaction_date"], errors="coerce")
    if "amount" in result.columns:
        result["amount"] = pd.to_numeric(result["amount"], errors="coerce")
    if "customer_id" in result.columns:
        result["customer_id"] = result["customer_id"].astype("string")
    if "acquisition_cost" in result.columns:
        result["acquisition_cost"] = pd.to_numeric(result["acquisition_cost"], errors="coerce")
    return result


def _format_value(value: float | int, metric_type: str) -> str:
    if metric_type == "currency":
        return f"${value:,.2f}"
    if metric_type == "percent":
        return f"{value:.1%}"
    if metric_type == "integer":
        return f"{int(round(value)):,}"
    return f"{value:,.2f}"


def calculate_mau(df: pd.DataFrame, days: int = 30, formatted: bool = False) -> int | str:
    """Monthly Active Users: distinct customers active in the last N days."""
    _require_columns(df, {"customer_id", "transaction_date"})
    data = _normalize_transactions(df)
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)
    value = int(data.loc[data["transaction_date"] >= cutoff, "customer_id"].nunique())
    return _format_value(value, "integer") if formatted else value


def calculate_revenue_per_customer(df: pd.DataFrame, formatted: bool = False) -> float | str:
    """Average revenue per unique customer."""
    _require_columns(df, {"customer_id", "amount"})
    data = _normalize_transactions(df)
    unique_customers = data["customer_id"].nunique()
    value = float(data["amount"].sum() / unique_customers) if unique_customers else 0.0
    return _format_value(value, "currency") if formatted else value


def calculate_churn_rate(df: pd.DataFrame, period_days: int = 30, formatted: bool = False) -> float | str:
    """Customers active in one period but not the next period."""
    _require_columns(df, {"customer_id", "transaction_date"})
    data = _normalize_transactions(df)

    period_1_end = pd.Timestamp.now() - pd.Timedelta(days=period_days)
    period_1_start = period_1_end - pd.Timedelta(days=period_days)
    period_2_end = pd.Timestamp.now()
    period_2_start = pd.Timestamp.now() - pd.Timedelta(days=period_days)

    active_p1 = set(
        data.loc[
            (data["transaction_date"] >= period_1_start) & (data["transaction_date"] <= period_1_end),
            "customer_id",
        ].dropna().astype("string")
    )
    active_p2 = set(
        data.loc[
            (data["transaction_date"] >= period_2_start) & (data["transaction_date"] <= period_2_end),
            "customer_id",
        ].dropna().astype("string")
    )

    if not active_p1:
        value = 0.0
    else:
        churned = len([customer_id for customer_id in active_p1 if customer_id not in active_p2])
        value = churned / len(active_p1)

    return _format_value(value, "percent") if formatted else float(value)


def calculate_payment_success_rate(df: pd.DataFrame, formatted: bool = False) -> float | str:
    """Successful payments divided by all payment attempts."""
    _require_columns(df, {"transaction_date"})
    if "payment_status" not in df.columns:
        raise KeyError("Missing required columns: ['payment_status']")

    statuses = df["payment_status"].astype("string").str.strip().str.lower()
    total_attempts = int(statuses.notna().sum())
    successful_attempts = int(statuses.isin({"success", "successful", "paid", "completed"}).sum())
    value = successful_attempts / total_attempts if total_attempts else 0.0
    return _format_value(value, "percent") if formatted else value


def calculate_customer_acquisition_cost(df: pd.DataFrame, formatted: bool = False) -> float | str:
    """Average acquisition cost per customer."""
    _require_columns(df, {"customer_id"})
    if "acquisition_cost" not in df.columns:
        raise KeyError("Missing required columns: ['acquisition_cost']")

    data = _normalize_transactions(df)
    unique_customers = data["customer_id"].nunique()
    value = float(data["acquisition_cost"].sum() / unique_customers) if unique_customers else 0.0
    return _format_value(value, "currency") if formatted else value


def calculate_repeat_purchase_rate(df: pd.DataFrame, formatted: bool = False) -> float | str:
    """Customers with more than one transaction divided by unique customers."""
    _require_columns(df, {"customer_id"})
    data = _normalize_transactions(df)
    purchase_counts = data.groupby("customer_id").size()
    unique_customers = int(purchase_counts.size)
    repeat_customers = int((purchase_counts > 1).sum())
    value = repeat_customers / unique_customers if unique_customers else 0.0
    return _format_value(value, "percent") if formatted else value


def calculate_average_order_value(df: pd.DataFrame, formatted: bool = False) -> float | str:
    """Average revenue per transaction."""
    _require_columns(df, {"amount"})
    data = _normalize_transactions(df)
    transaction_count = int(data["amount"].count())
    value = float(data["amount"].sum() / transaction_count) if transaction_count else 0.0
    return _format_value(value, "currency") if formatted else value


def compute_all_kpis(df: pd.DataFrame) -> dict[str, float]:
    """Return a reusable raw KPI snapshot for validation or dashboards."""
    return {
        "monthly_active_users": float(calculate_mau(df)),
        "revenue_per_customer": float(calculate_revenue_per_customer(df)),
        "churn_rate": float(calculate_churn_rate(df)),
        "payment_success_rate": float(calculate_payment_success_rate(df)),
        "customer_acquisition_cost": float(calculate_customer_acquisition_cost(df)),
        "repeat_purchase_rate": float(calculate_repeat_purchase_rate(df)),
        "average_order_value": float(calculate_average_order_value(df)),
    }


def validate_kpis(current_kpis: dict[str, float], targets: dict[str, dict[str, float]]) -> pd.DataFrame:
    """Compare KPI values against target ranges and return a validation table."""
    validation_rows: list[dict[str, float | str]] = []

    for kpi_name, target_range in targets.items():
        actual = float(current_kpis[kpi_name])
        minimum = float(target_range["min"])
        maximum = float(target_range["max"])
        status = "PASS" if minimum <= actual <= maximum else "ALERT"
        validation_rows.append(
            {
                "kpi": kpi_name,
                "actual": actual,
                "target_min": minimum,
                "target_max": maximum,
                "status": status,
            }
        )

    return pd.DataFrame(validation_rows)


def load_validation_targets(target_path: str | Path | None = None) -> dict[str, dict[str, float]]:
    """Load KPI target ranges from JSON so they can be updated without code changes."""
    if target_path is None:
        target_path = Path(__file__).resolve().parent / "kpi_validation_targets.json"
    target_file = Path(target_path)

    with open(target_file, "r", encoding="utf-8") as handle:
        return json.load(handle)


def build_revenue_decomposition(df: pd.DataFrame) -> dict[str, object]:
    """Break total revenue into top-level, segment, and product components."""
    _require_columns(df, {"amount"})
    data = _normalize_transactions(df)

    total_revenue = float(data["amount"].sum())
    revenue_by_segment = data.groupby("customer_type")["amount"].sum() if "customer_type" in data.columns else pd.Series(dtype=float)
    revenue_by_product = data.groupby("product")["amount"].sum() if "product" in data.columns else pd.Series(dtype=float)

    customer_counts = data["customer_id"].nunique() if "customer_id" in data.columns else 0
    segment_customer_counts = (
        data.groupby("customer_type")["customer_id"].nunique() if "customer_type" in data.columns and "customer_id" in data.columns else pd.Series(dtype=float)
    )

    return {
        "total_revenue": total_revenue,
        "revenue_by_segment": revenue_by_segment,
        "revenue_by_product": revenue_by_product,
        "unique_customers": int(customer_counts),
        "customers_by_segment": segment_customer_counts,
    }


def format_revenue_decomposition(df: pd.DataFrame) -> str:
    """Return a readable hierarchy for the revenue decomposition example."""
    decomposition = build_revenue_decomposition(df)
    revenue_by_segment = decomposition["revenue_by_segment"]
    revenue_by_product = decomposition["revenue_by_product"]

    segment_lines = "\n".join(
        f"  {segment}: ${value:,.0f}" for segment, value in revenue_by_segment.items()
    ) if len(revenue_by_segment) else "  No customer_type column available"

    product_lines = revenue_by_product.to_string() if len(revenue_by_product) else "No product column available"

    return (
        "KPI DECOMPOSITION: Total Monthly Revenue\n\n"
        f"Level 1 (Top-level): ${decomposition['total_revenue']:,.0f}\n\n"
        "Level 2 (By Segment):\n"
        f"{segment_lines}\n\n"
        "Level 3 (By Product within Segment):\n"
        f"{product_lines}"
    )


__all__ = [
    "calculate_mau",
    "calculate_revenue_per_customer",
    "calculate_churn_rate",
    "calculate_payment_success_rate",
    "calculate_customer_acquisition_cost",
    "calculate_repeat_purchase_rate",
    "calculate_average_order_value",
    "compute_all_kpis",
    "validate_kpis",
    "load_validation_targets",
    "build_revenue_decomposition",
    "format_revenue_decomposition",
]
