import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "data" / "raw"
DEFAULT_DB_PATH = ROOT_DIR / "data" / "join_validation.db"
DEFAULT_REPORT_PATH = ROOT_DIR / "output" / "join_validation_report.md"


def load_demo_data() -> dict[str, pd.DataFrame]:
    customers = pd.read_csv(RAW_DIR / "customers.csv").copy()

    if "customer_type" not in customers.columns:
        customers["customer_type"] = np.where(
            customers["customer_id"] % 2 == 0,
            "Enterprise",
            "SMB",
        )

    if "signup_date" in customers.columns:
        customers["signup_date"] = pd.to_datetime(customers["signup_date"]).dt.strftime("%Y-%m-%d")

    orders = pd.read_json(RAW_DIR / "transactions.json")
    orders = orders.rename(
        columns={"id": "order_id", "amount": "order_amount", "status": "order_status"}
    ).copy()
    orders["order_date"] = pd.Timestamp("2025-04-01") + pd.to_timedelta(orders["order_id"], unit="D")
    orders["order_date"] = orders["order_date"].dt.strftime("%Y-%m-%d")

    order_items = pd.DataFrame(
        [
            {"order_item_id": 1, "order_id": 1, "product_id": 101, "quantity": 1, "unit_price": 100.0},
            {"order_item_id": 2, "order_id": 1, "product_id": 102, "quantity": 1, "unit_price": 25.0},
            {"order_item_id": 3, "order_id": 2, "product_id": 103, "quantity": 2, "unit_price": 125.0},
            {"order_item_id": 4, "order_id": 3, "product_id": 104, "quantity": 1, "unit_price": 150.0},
        ]
    )

    products = pd.DataFrame(
        [
            {"product_id": 101, "product_name": "Laptop Stand"},
            {"product_id": 102, "product_name": "Keyboard"},
            {"product_id": 103, "product_name": "Docking Station"},
            {"product_id": 104, "product_name": "Monitor"},
        ]
    )

    return {
        "customers": customers,
        "orders": orders,
        "order_items": order_items,
        "products": products,
    }


def load_existing_or_demo_database(db_path: Path) -> tuple[sqlite3.Connection, str]:
    if db_path.exists():
        conn = sqlite3.connect(db_path)
        existing_tables = {
            name
            for (name,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        if {"customers", "orders", "order_items", "products"}.issubset(existing_tables):
            return conn, "existing"
        conn.close()

    conn = sqlite3.connect(":memory:")
    for table_name, frame in load_demo_data().items():
        frame.to_sql(table_name, conn, index=False, if_exists="replace")
    return conn, "demo"


def sql_count(conn: sqlite3.Connection, query: str) -> int:
    return int(pd.read_sql_query(query, conn).iloc[0, 0])


def validate_left_join(conn: sqlite3.Connection) -> dict[str, object]:
    customers_count = sql_count(conn, "SELECT COUNT(*) FROM customers")
    orders_count = sql_count(conn, "SELECT COUNT(*) FROM orders")
    grouped = pd.read_sql_query(
        """
        SELECT
            c.customer_id,
            c.customer_type,
            COUNT(DISTINCT o.order_id) AS order_count,
            SUM(o.order_amount) AS total_spent
        FROM customers c
        LEFT JOIN orders o ON c.customer_id = o.customer_id
        GROUP BY c.customer_id, c.customer_type
        ORDER BY total_spent DESC NULLS LAST
        """,
        conn,
    )
    left_join_rows = sql_count(
        conn,
        """
        SELECT COUNT(*)
        FROM customers c
        LEFT JOIN orders o ON c.customer_id = o.customer_id
        """,
    )
    return {
        "customers_count": customers_count,
        "orders_count": orders_count,
        "grouped_rows": len(grouped),
        "left_join_rows": left_join_rows,
        "orders_per_customer": orders_count / customers_count if customers_count else 0,
        "result": grouped,
    }


def validate_unmatched_keys(conn: sqlite3.Connection) -> dict[str, pd.DataFrame]:
    no_orders = pd.read_sql_query(
        """
        SELECT c.customer_id, c.customer_type, c.signup_date
        FROM customers c
        LEFT JOIN orders o ON c.customer_id = o.customer_id
        WHERE o.order_id IS NULL
        ORDER BY c.signup_date
        """,
        conn,
    )

    orphaned = pd.read_sql_query(
        """
        SELECT o.order_id, o.customer_id, o.order_date
        FROM orders o
        LEFT JOIN customers c ON o.customer_id = c.customer_id
        WHERE c.customer_id IS NULL
        ORDER BY o.order_date
        """,
        conn,
    )

    return {"no_orders": no_orders, "orphaned": orphaned}


def compare_join_types(conn: sqlite3.Connection) -> dict[str, int]:
    inner = sql_count(
        conn,
        """
        SELECT COUNT(*)
        FROM customers c
        INNER JOIN orders o ON c.customer_id = o.customer_id
        """,
    )
    left = sql_count(
        conn,
        """
        SELECT COUNT(*)
        FROM customers c
        LEFT JOIN orders o ON c.customer_id = o.customer_id
        """,
    )
    full = sql_count(
        conn,
        """
        WITH left_side AS (
            SELECT c.customer_id, o.order_id
            FROM customers c
            LEFT JOIN orders o ON c.customer_id = o.customer_id
        ),
        right_only AS (
            SELECT c.customer_id, o.order_id
            FROM orders o
            LEFT JOIN customers c ON c.customer_id = o.customer_id
            WHERE c.customer_id IS NULL
        )
        SELECT COUNT(*)
        FROM (
            SELECT * FROM left_side
            UNION ALL
            SELECT * FROM right_only
        )
        """,
    )
    return {"inner": inner, "left": left, "full": full}


def validate_multi_table_join(conn: sqlite3.Connection) -> dict[str, object]:
    result = pd.read_sql_query(
        """
        SELECT
            c.customer_id,
            c.customer_type,
            o.order_id,
            o.order_date,
            oi.product_id,
            p.product_name,
            oi.quantity,
            oi.unit_price,
            (oi.quantity * oi.unit_price) AS line_total
        FROM customers c
        LEFT JOIN orders o ON c.customer_id = o.customer_id
        LEFT JOIN order_items oi ON o.order_id = oi.order_id
        LEFT JOIN products p ON oi.product_id = p.product_id
        WHERE c.customer_type = 'Enterprise'
        ORDER BY o.order_date DESC
        """,
        conn,
    )
    expected_total = float(
        pd.read_sql_query(
            """
            SELECT SUM(oi.quantity * oi.unit_price) AS total
            FROM customers c
            LEFT JOIN orders o ON c.customer_id = o.customer_id
            LEFT JOIN order_items oi ON o.order_id = oi.order_id
            WHERE c.customer_type = 'Enterprise'
            """,
            conn,
        ).iloc[0, 0]
    )
    joined_total = float(result["line_total"].fillna(0).sum())
    return {
        "result_rows": len(result),
        "joined_total": joined_total,
        "expected_total": expected_total,
        "result": result,
    }


def build_report(mode: str, left_summary: dict[str, object], unmatched: dict[str, pd.DataFrame], join_types: dict[str, int], multi_summary: dict[str, object]) -> str:
    no_orders = unmatched["no_orders"]
    orphaned = unmatched["orphaned"]

    lines = [
        "# Join Validation Report",
        "",
        f"Data mode: {mode}",
        f"Customers: {left_summary['customers_count']}",
        f"Orders: {left_summary['orders_count']}",
        "",
        "## Task 1: LEFT JOIN with Row Count Validation",
        f"Customer groups returned: {left_summary['grouped_rows']}",
        f"Raw LEFT JOIN row count: {left_summary['left_join_rows']}",
        f"Average orders per customer: {left_summary['orders_per_customer']:.2f}",
        "",
        "Why the result grows: this is a one-to-many join. Customers with multiple orders are repeated once per order, and customers without orders remain in the result with NULL order fields.",
        "",
        "## Task 2: Unmatched Keys",
        f"Customers with no orders: {len(no_orders)}",
        f"Orphaned orders: {len(orphaned)}",
        "",
        "## Task 3: Join Type Comparison",
        f"INNER rows: {join_types['inner']}",
        f"LEFT rows: {join_types['left']}",
        f"FULL rows: {join_types['full']}",
        "",
        "## Task 4: Multi-Table Join",
        f"Rows returned: {multi_summary['result_rows']}",
        f"Joined line total: {multi_summary['joined_total']:.2f}",
        f"Expected line-item total: {multi_summary['expected_total']:.2f}",
        "",
        "## Task 5: Join Decisions",
        "- LEFT JOIN from customers to orders keeps every customer in the analysis and exposes customers without orders as NULL matches.",
        "- INNER JOIN is for matched-record analysis where missing keys should be excluded.",
        "- FULL OUTER JOIN is for reconciliation because it retains both unmatched customers and unmatched orders.",
        "- Multi-table LEFT JOINs are useful for lineage, but downstream aggregations must be done carefully to avoid double-counting at the line-item level.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    conn, mode = load_existing_or_demo_database(DEFAULT_DB_PATH)
    try:
        left_summary = validate_left_join(conn)
        unmatched = validate_unmatched_keys(conn)
        join_types = compare_join_types(conn)
        multi_summary = validate_multi_table_join(conn)

        report = build_report(mode, left_summary, unmatched, join_types, multi_summary)
        DEFAULT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_REPORT_PATH.write_text(report, encoding="utf-8")

        print(report)
        print(f"Report saved to: {DEFAULT_REPORT_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()