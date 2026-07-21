"""Compare inefficient analytical SQL with refactored versions.

This script builds a local SQLite demo database, runs each original and optimized
query side-by-side, and records the performance and readability improvements.
It focuses on three patterns:

1. Removing SELECT * in favour of explicit columns.
2. Filtering early in a CTE before joining to larger tables.
3. Replacing nested subqueries with named CTEs for clarity and reuse.
"""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT_DIR / "output"
REPORT_PATH = OUTPUT_DIR / "sql_optimization_comparison.md"


@dataclass
class QueryRun:
    rows: int
    columns: int
    elapsed_seconds: float
    memory_bytes: int
    dataframe: pd.DataFrame


def build_demo_database() -> sqlite3.Connection:
    """Build a reproducible SQLite dataset for analytical query refactoring.

    The demo schema mirrors the business questions in the assignment:
    transactions feed customer-revenue analysis, customers provide segment and
    geography context, and products support join-heavy reporting.
    """

    rng = np.random.default_rng(42)
    conn = sqlite3.connect(":memory:")

    customers = pd.DataFrame(
        {
            "id": np.arange(1, 5001),
            "customer_name": [f"Customer {i}" for i in range(1, 5001)],
            "country": rng.choice(["USA", "Canada", "UK", "Germany", "India"], size=5000, p=[0.42, 0.16, 0.16, 0.13, 0.13]),
            "account_type": rng.choice(["Enterprise", "Mid-Market", "SMB", "Starter"], size=5000, p=[0.18, 0.27, 0.38, 0.17]),
            "customer_segment": rng.choice(["Enterprise", "Mid-Market", "SMB", "Starter"], size=5000, p=[0.18, 0.27, 0.38, 0.17]),
        }
    )

    products = pd.DataFrame(
        {
            "id": np.arange(1, 1001),
            "product_name": [f"Product {i}" for i in range(1, 1001)],
            "category": rng.choice(["Hardware", "Software", "Services", "Accessories"], size=1000),
        }
    )

    transaction_count = 40000
    transaction_dates = pd.date_range("2023-01-01", "2024-12-31", periods=transaction_count)
    transactions = pd.DataFrame(
        {
            "transaction_id": np.arange(1, transaction_count + 1),
            "transaction_date": transaction_dates.strftime("%Y-%m-%d"),
            "amount": np.round(rng.lognormal(mean=4.25, sigma=0.6, size=transaction_count), 2),
            "customer_id": rng.integers(1, 5001, size=transaction_count),
            "product_id": rng.integers(1, 1001, size=transaction_count),
            "channel": rng.choice(["web", "sales", "partner", "mobile"], size=transaction_count),
            "status": rng.choice(["completed", "pending", "refunded"], size=transaction_count, p=[0.82, 0.12, 0.06]),
            "region": rng.choice(["North", "South", "East", "West"], size=transaction_count),
            "sales_rep": rng.choice(["Rep A", "Rep B", "Rep C", "Rep D", "Rep E"], size=transaction_count),
            "promo_code": rng.choice(["NONE", "WELCOME10", "SAVE20", "VIP30"], size=transaction_count, p=[0.58, 0.18, 0.16, 0.08]),
            "payment_method": rng.choice(["card", "bank_transfer", "paypal", "invoice"], size=transaction_count),
            "loyalty_tier": rng.choice(["Bronze", "Silver", "Gold", "Platinum"], size=transaction_count),
        }
    )

    customers.to_sql("customers", conn, index=False, if_exists="replace")
    products.to_sql("products", conn, index=False, if_exists="replace")
    transactions.to_sql("transactions", conn, index=False, if_exists="replace")

    return conn


def fetch_query(conn: sqlite3.Connection, query: str) -> QueryRun:
    start = time.perf_counter()
    dataframe = pd.read_sql_query(query, conn)
    elapsed_seconds = time.perf_counter() - start
    memory_bytes = int(dataframe.memory_usage(deep=True).sum())
    return QueryRun(
        rows=len(dataframe),
        columns=len(dataframe.columns),
        elapsed_seconds=elapsed_seconds,
        memory_bytes=memory_bytes,
        dataframe=dataframe,
    )


def compare_frames(left: pd.DataFrame, right: pd.DataFrame) -> bool:
    if list(left.columns) != list(right.columns):
        return False
    left_sorted = left.sort_values(by=list(left.columns)).reset_index(drop=True)
    right_sorted = right.sort_values(by=list(right.columns)).reset_index(drop=True)
    return left_sorted.equals(right_sorted)


def format_mb(value: int) -> str:
    return f"{value / (1024 ** 2):.2f} MB"


def build_report(section_1: dict[str, object], section_2: dict[str, object], section_3: dict[str, object]) -> str:
    comparison = pd.DataFrame(
        {
            "Metric": [
                "Columns Selected",
                "Intermediate Rows",
                "Filters Applied Before Join",
                "Nesting Depth",
                "Readability Score",
            ],
            "Original": ["SELECT *", section_2["transactions_count"], "No", "3 levels", "Hard to follow"],
            "Optimized": [f"{section_1['optimized_columns']} explicit", f"{section_2['filtered_transactions_count']}", "Yes", "1 level (CTEs)", "Clear steps"],
        }
    )

    report = [
        "# SQL Optimization Comparison",
        "",
        "## Summary Table",
        comparison.to_string(index=False),
        "",
        "## Task 1 - Remove SELECT *",
        "Original query:",
        "```sql",
        section_1["original_query"].strip(),
        "```",
        "Optimized query:",
        "```sql",
        section_1["optimized_query"].strip(),
        "```",
        f"Original columns: {section_1['original_columns']}",
        f"Optimized columns: {section_1['optimized_columns']}",
        f"Same core data: {section_1['same_core_data']}",
        f"Original time: {section_1['original_time']:.4f}s",
        f"Optimized time: {section_1['optimized_time']:.4f}s",
        f"Original memory: {section_1['original_memory']}",
        f"Optimized memory: {section_1['optimized_memory']}",
        f"Memory reduction: {section_1['memory_savings_pct']:.1f}%",
        f"Column reduction: {section_1['column_reduction_pct']:.1f}%",
        "",
        "## Task 2 - Filter Before JOIN",
        "Original query:",
        "```sql",
        section_2["original_query"].strip(),
        "```",
        "Optimized query:",
        "```sql",
        section_2["optimized_query"].strip(),
        "```",
        f"Transactions table size: {section_2['transactions_count']:,}",
        f"Filtered transactions before join: {section_2['filtered_transactions_count']:,}",
        f"Reduction factor before join: {section_2['reduction_factor']:.2f}x",
        f"Final row count: {section_2['final_rows']:,}",
        f"Results identical: {section_2['same_results']}",
        "",
        "## Task 3 - CTEs for Readability",
        "Original query:",
        "```sql",
        section_3["original_query"].strip(),
        "```",
        "Refactored query:",
        "```sql",
        section_3["refactored_query"].strip(),
        "```",
        f"Results identical: {section_3['same_results']}",
        f"Original time: {section_3['original_time']:.4f}s",
        f"Refactored time: {section_3['optimized_time']:.4f}s",
        "",
        "## Specific Improvements Identified",
        "- Query 1 removed SELECT * so the database returns only the columns the dashboard or report actually needs.",
        "- Query 2 pushes filters into a CTE so the join operates on a smaller working set.",
        "- Query 3 replaces deep nesting with named CTEs so each step can be read and tested independently.",
        "",
        "## Best Practices Applied",
        "- Explicit column selection: reduces payload size, memory use, and accidental dependency on unused fields.",
        "- Early filtering: limits intermediate join volume and lowers CPU and I/O cost.",
        "- CTE structuring: improves maintainability and makes the transformation pipeline easier to validate.",
        "",
        "## Follow-Up Answers",
        "1. An index on a high-cardinality filter column can speed reads because the engine can locate matching rows without scanning the full table. The tradeoff is extra storage and slower writes, because the index must be maintained on insert, update, and delete.",
        "2. In SQLite, a CTE is primarily a query-planner construct. Depending on how it is used, the planner may inline it or materialize it, so repeated references are not something I would assume blindly. The practical lesson is to use CTEs for clarity first, and verify plans when reuse matters.",
        "3. If the filtered set is still huge, the next tools are partitioning, materialized views, pre-aggregated tables, and carefully chosen indexes. You can also denormalize analytical models or move heavy computation into scheduled ETL instead of doing it at query time.",
    ]
    return "\n".join(report) + "\n"


def section_1_select_star(conn: sqlite3.Connection) -> dict[str, object]:
    original_query = """
    SELECT *
    FROM transactions t
    JOIN customers c ON t.customer_id = c.id
    WHERE strftime('%Y', t.transaction_date) = '2024'
    LIMIT 1000;
    """

    optimized_query = """
    SELECT
        t.transaction_id,      -- business question: which transaction happened?
        t.transaction_date,    -- business question: when did it happen?
        t.amount,              -- business question: how much revenue was recorded?
        t.customer_id,         -- business question: which customer generated it?
        c.customer_name,       -- business question: who is the customer?
        c.country,             -- business question: where is the customer located?
        c.account_type         -- business question: what account tier is this?
    FROM transactions t
    JOIN customers c ON t.customer_id = c.id
    WHERE strftime('%Y', t.transaction_date) = '2024'
    LIMIT 1000;
    """

    original_run = fetch_query(conn, original_query)
    optimized_run = fetch_query(conn, optimized_query)

    original_core = original_run.dataframe[
        ["transaction_id", "transaction_date", "amount", "customer_id", "customer_name", "country", "account_type"]
    ].copy()
    same_core_data = compare_frames(original_core, optimized_run.dataframe)

    return {
        "original_query": original_query,
        "optimized_query": optimized_query,
        "original_columns": original_run.columns,
        "optimized_columns": optimized_run.columns,
        "original_time": original_run.elapsed_seconds,
        "optimized_time": optimized_run.elapsed_seconds,
        "original_memory": format_mb(original_run.memory_bytes),
        "optimized_memory": format_mb(optimized_run.memory_bytes),
        "memory_savings_pct": ((original_run.memory_bytes - optimized_run.memory_bytes) / original_run.memory_bytes * 100) if original_run.memory_bytes else 0.0,
        "column_reduction_pct": ((original_run.columns - optimized_run.columns) / original_run.columns * 100) if original_run.columns else 0.0,
        "same_core_data": same_core_data,
        "optimized_columns": optimized_run.columns,
    }


def section_2_filter_before_join(conn: sqlite3.Connection) -> dict[str, object]:
    original_query = """
    SELECT t.transaction_id, t.amount, c.customer_name, p.product_name
    FROM transactions t
    JOIN customers c ON t.customer_id = c.id
    JOIN products p ON t.product_id = p.id
    WHERE t.transaction_date >= '2024-01-01'
      AND t.amount > 100
      AND c.country = 'USA'
    LIMIT 5000;
    """

    optimized_query = """
    WITH filtered_trans AS (
        SELECT transaction_id, customer_id, product_id, transaction_date, amount
        FROM transactions
        WHERE transaction_date >= '2024-01-01'
          AND amount > 100
    )
    SELECT ft.transaction_id, ft.amount, c.customer_name, p.product_name
    FROM filtered_trans ft
    JOIN customers c ON ft.customer_id = c.id
    JOIN products p ON ft.product_id = p.id
    WHERE c.country = 'USA'
    LIMIT 5000;
    """

    transactions_count = int(pd.read_sql_query("SELECT COUNT(*) AS count FROM transactions", conn).iloc[0, 0])
    filtered_transactions_count = int(
        pd.read_sql_query(
            """
            SELECT COUNT(*) AS count
            FROM transactions
            WHERE transaction_date >= '2024-01-01'
              AND amount > 100
            """,
            conn,
        ).iloc[0, 0]
    )

    original_run = fetch_query(conn, original_query)
    optimized_run = fetch_query(conn, optimized_query)

    same_results = compare_frames(original_run.dataframe, optimized_run.dataframe)
    reduction_factor = transactions_count / filtered_transactions_count if filtered_transactions_count else float("inf")

    return {
        "original_query": original_query,
        "optimized_query": optimized_query,
        "transactions_count": transactions_count,
        "filtered_transactions_count": filtered_transactions_count,
        "reduction_factor": reduction_factor,
        "final_rows": optimized_run.rows,
        "same_results": same_results,
    }


def section_3_ctes(conn: sqlite3.Connection) -> dict[str, object]:
    original_query = """
    SELECT customer_segment, AVG(revenue_per_transaction) AS avg_transaction_value
    FROM (
        SELECT
            c.customer_segment,
            AVG(t.amount) AS revenue_per_transaction,
            COUNT(DISTINCT t.transaction_id) AS transaction_count
        FROM (
            SELECT t.transaction_id, t.amount, t.customer_id
            FROM transactions t
            WHERE t.transaction_date >= '2024-01-01'
        ) t
        JOIN customers c ON t.customer_id = c.id
        GROUP BY c.customer_segment
    ) grouped
    GROUP BY customer_segment
    ORDER BY avg_transaction_value DESC;
    """

    refactored_query = """
    WITH recent_transactions AS (
        -- Step 1: Filter to recent data.
        SELECT transaction_id, amount, customer_id
        FROM transactions
        WHERE transaction_date >= '2024-01-01'
    ),
    customer_with_segment AS (
        -- Step 2: Join the filtered transactions to customer dimensions.
        SELECT
            rt.transaction_id,
            rt.amount,
            c.customer_segment
        FROM recent_transactions rt
        JOIN customers c ON rt.customer_id = c.id
    ),
    segment_metrics AS (
        -- Step 3: Aggregate to the segment level.
        SELECT
            customer_segment,
            COUNT(DISTINCT transaction_id) AS transaction_count,
            AVG(amount) AS avg_transaction_value,
            SUM(amount) AS total_revenue
        FROM customer_with_segment
        GROUP BY customer_segment
    )
    SELECT
        customer_segment,
        avg_transaction_value
    FROM segment_metrics
    ORDER BY avg_transaction_value DESC;
    """

    original_run = fetch_query(conn, original_query)
    refactored_run = fetch_query(conn, refactored_query)

    return {
        "original_query": original_query,
        "refactored_query": refactored_query,
        "same_results": compare_frames(original_run.dataframe, refactored_run.dataframe),
        "original_time": original_run.elapsed_seconds,
        "optimized_time": refactored_run.elapsed_seconds,
    }


def main() -> None:
    conn = build_demo_database()
    try:
        section_1 = section_1_select_star(conn)
        section_2 = section_2_filter_before_join(conn)
        section_3 = section_3_ctes(conn)

        report_text = build_report(section_1, section_2, section_3)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(report_text, encoding="utf-8")

        print(report_text)
        print(f"Report saved to: {REPORT_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()