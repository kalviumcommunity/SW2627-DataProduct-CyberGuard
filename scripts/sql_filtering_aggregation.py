# -*- coding: utf-8 -*-
from __future__ import annotations

"""
sql_filtering_aggregation.py
============================
SQL Filtering, Grouping & Aggregation -- Assignment 2.39
CyberGuard Data Product

"Show Enterprise customers with >$10k annual spending" -- do you filter
before or after grouping?  This module answers definitively with 5 queries
demonstrating WHERE, GROUP BY, HAVING, ORDER BY, and their combinations.

Tasks
-----
Task 1 -- WHERE Filtering        (queries/where_filtering.sql)
Task 2 -- GROUP BY Aggregation   (queries/groupby_aggregation.sql)
Task 3 -- HAVING Filtering       (queries/having_filtering.sql)
Task 4 -- WHERE + HAVING         (queries/where_having_combined.sql)
Task 5 -- ORDER BY Ranking       (queries/orderby_ranking.sql)
"""

import sys
import io
from pathlib import Path

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text

# ── Force UTF-8 on Windows ────────────────────────────────────────────────────
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parents[1]
DB_PATH     = BASE_DIR / "data" / "cyberguard.db"
QUERIES_DIR = BASE_DIR / "queries"

CONNECTION_STRING = f"sqlite:///{DB_PATH}"
RNG = np.random.default_rng(42)


# =============================================================================
# HELPER -- Load a .sql query file
# =============================================================================
def load_query(query_name: str) -> str:
    """Read SQL from queries/<query_name>.sql and return as string.

    Parameters
    ----------
    query_name : str
        Filename stem, e.g. 'where_filtering' (no extension).

    Returns
    -------
    str
        Raw SQL ready for pd.read_sql().
    """
    path = QUERIES_DIR / f"{query_name}.sql"
    if not path.exists():
        raise FileNotFoundError(f"Query file not found: {path}")
    return path.read_text(encoding="utf-8")


# =============================================================================
# SEED -- Build transactions / customers tables with realistic business data
# =============================================================================
def seed_tables(engine) -> None:
    """Seed customers, transactions tables with synthetic data.

    Columns mirror the assignment's schema expectations:
      transactions: order_id, customer_id, customer_type,
                    transaction_date, amount, transaction_status
      customers:    customer_id, customer_type, lifetime_value,
                    churn, support_tickets, retention_days
    """
    n_cust = 600
    cust_ids   = np.arange(1001, 1001 + n_cust)
    cust_types = RNG.choice(
        ["Enterprise", "SMB", "Startup"],
        size=n_cust,
        p=[0.15, 0.30, 0.55],
    )

    customers_df = pd.DataFrame({
        "customer_id":    cust_ids,
        "customer_type":  cust_types,
        "lifetime_value": np.where(
            cust_types == "Enterprise",
            RNG.uniform(80_000, 200_000, n_cust),
            np.where(cust_types == "SMB",
                     RNG.uniform(5_000, 30_000, n_cust),
                     RNG.uniform(500, 5_000, n_cust)),
        ).round(2),
        "churn": (RNG.random(n_cust) < np.where(
            cust_types == "Enterprise", 0.02,
            np.where(cust_types == "SMB", 0.12, 0.20),
        )).astype(int),
        "support_tickets": RNG.integers(0, 6, n_cust),
        "retention_days":  RNG.integers(30, 900, n_cust),
    })
    customers_df.to_sql("customers", engine, if_exists="replace", index=False)
    print(f"  [seeded] customers    : {len(customers_df):>5} rows")

    # -- Transactions --------------------------------------------------------
    n_tx = 10_000
    tx_cust_ids = RNG.choice(cust_ids, size=n_tx)
    ctype_map   = dict(zip(cust_ids, cust_types))
    tx_types    = [ctype_map[c] for c in tx_cust_ids]

    # Span 2 years so queries with DATE '2024-01-01' boundary show a real split
    base = pd.Timestamp("2025-12-31")
    days_back  = RNG.integers(0, 730, n_tx)   # up to 2 years back
    tx_dates   = base - pd.to_timedelta(days_back, unit="D")

    amounts = np.where(
        np.array(tx_types) == "Enterprise",
        RNG.uniform(2_000, 15_000, n_tx),
        np.where(np.array(tx_types) == "SMB",
                 RNG.uniform(300, 3_000, n_tx),
                 RNG.uniform(50, 600, n_tx)),
    ).round(2)

    # Mix of statuses: ~85% completed, ~10% failed, ~5% pending
    statuses = RNG.choice(
        ["completed", "failed", "pending"],
        size=n_tx,
        p=[0.85, 0.10, 0.05],
    )

    transactions_df = pd.DataFrame({
        "order_id":          np.arange(20001, 20001 + n_tx),
        "customer_id":       tx_cust_ids,
        "customer_type":     tx_types,
        "transaction_date":  tx_dates,
        "amount":            amounts,
        "transaction_status": statuses,
    })
    transactions_df.to_sql("transactions", engine, if_exists="replace", index=False)
    print(f"  [seeded] transactions : {len(transactions_df):>5} rows")
    print()


# =============================================================================
# TASK 1 -- WHERE Filtering (SQLite-compatible)
# =============================================================================
def task1_where_filtering(engine) -> pd.DataFrame:
    """Mirrors queries/where_filtering.sql using SQLite date syntax."""
    sql = """
        SELECT
            customer_id,
            COUNT(*)               AS transaction_count,
            ROUND(SUM(amount), 2)  AS annual_revenue,
            ROUND(AVG(amount), 2)  AS avg_transaction_value
        FROM transactions
        WHERE transaction_date >= '2024-01-01'   -- Restrict to analysis year
          AND transaction_date <  '2025-01-01'   -- Upper boundary
          AND amount > 0                         -- Remove refunds / zero rows
          AND transaction_status = 'completed'   -- Valid transactions only
        GROUP BY customer_id
        ORDER BY annual_revenue DESC
    """
    return pd.read_sql(sql, engine)


# =============================================================================
# TASK 2 -- GROUP BY and Aggregation (SQLite-compatible)
# =============================================================================
def task2_groupby_aggregation(engine) -> pd.DataFrame:
    """Mirrors queries/groupby_aggregation.sql using SQLite strftime."""
    sql = """
        SELECT
            c.customer_type,
            strftime('%Y-%m-01', t.transaction_date)  AS month,
            COUNT(DISTINCT t.customer_id)             AS unique_customers,
            COUNT(*)                                  AS transaction_count,
            ROUND(SUM(t.amount), 2)                   AS monthly_revenue,
            ROUND(AVG(t.amount), 2)                   AS avg_transaction
        FROM transactions t
        JOIN customers c ON t.customer_id = c.customer_id
        WHERE t.transaction_date >= '2024-01-01'
          AND t.transaction_status = 'completed'
        GROUP BY c.customer_type,
                 strftime('%Y-%m-01', t.transaction_date)
        ORDER BY month DESC, monthly_revenue DESC
    """
    return pd.read_sql(sql, engine)


# =============================================================================
# TASK 3 -- HAVING Filtering (SQLite-compatible)
# =============================================================================
def task3_having_filtering(engine) -> pd.DataFrame:
    """Mirrors queries/having_filtering.sql."""
    sql = """
        SELECT
            customer_id,
            COUNT(*)              AS transaction_count,
            ROUND(SUM(amount), 2) AS annual_revenue
        FROM transactions
        WHERE transaction_date >= '2024-01-01'
        GROUP BY customer_id
        HAVING SUM(amount)  > 10000   -- HAVING: high-value customers only
           AND COUNT(*)    >= 5        -- HAVING: engaged customers (5+ purchases)
        ORDER BY annual_revenue DESC
    """
    return pd.read_sql(sql, engine)


# =============================================================================
# TASK 4 -- WHERE + HAVING Combined (SQLite-compatible)
# =============================================================================
def task4_where_having_combined(engine) -> pd.DataFrame:
    """Mirrors queries/where_having_combined.sql (without window SUM OVER)."""
    # SQLite lacks SUM() OVER() in older versions; compute share in Python.
    sql = """
        SELECT
            c.customer_type,
            COUNT(DISTINCT t.customer_id)  AS segment_customers,
            COUNT(*)                       AS order_count,
            ROUND(SUM(t.amount), 2)        AS segment_revenue,
            ROUND(AVG(t.amount), 2)        AS avg_order_value
        FROM transactions t
        JOIN customers c ON t.customer_id = c.customer_id
        WHERE t.transaction_date >= '2024-01-01'      -- WHERE: analysis window
          AND t.transaction_status = 'completed'      -- WHERE: data quality
          AND t.amount > 0                            -- WHERE: logical validity
        GROUP BY c.customer_type
        HAVING COUNT(DISTINCT t.customer_id) >= 10    -- HAVING: meaningful segment
           AND SUM(t.amount) > 0                      -- HAVING: non-zero revenue
        ORDER BY segment_revenue DESC
    """
    df = pd.read_sql(sql, engine)
    total = df["segment_revenue"].sum()
    df["revenue_share_pct"] = (df["segment_revenue"] / total * 100).round(2)
    return df


# =============================================================================
# TASK 5 -- ORDER BY Ranking (SQLite-compatible)
# =============================================================================
def task5_orderby_ranking(engine) -> pd.DataFrame:
    """Mirrors queries/orderby_ranking.sql (RANK via pandas rank)."""
    sql = """
        SELECT
            c.customer_type,
            COUNT(DISTINCT t.customer_id)  AS customers,
            COUNT(*)                       AS total_orders,
            ROUND(SUM(t.amount), 2)        AS total_revenue,
            ROUND(AVG(t.amount), 2)        AS avg_order
        FROM transactions t
        JOIN customers c ON t.customer_id = c.customer_id
        WHERE t.transaction_date >= '2024-01-01'
          AND t.transaction_status = 'completed'
          AND t.amount > 0
        GROUP BY c.customer_type
        HAVING COUNT(DISTINCT t.customer_id) >= 10
        ORDER BY total_revenue DESC
        LIMIT 20
    """
    df = pd.read_sql(sql, engine)
    # Apply ranking in pandas (mirrors RANK() OVER ... in PostgreSQL)
    df["revenue_rank"] = df["total_revenue"].rank(
        method="min", ascending=False
    ).astype(int)
    df["customer_count_rank"] = df["customers"].rank(
        method="dense", ascending=False
    ).astype(int)
    return df


# =============================================================================
# Print helper
# =============================================================================
def _print_result(title: str, df: pd.DataFrame, head: int = 10) -> None:
    print(f"  {title} ({len(df)} rows):")
    print(df.head(head).to_string(index=False))
    print()


# =============================================================================
# Validate -- basic sanity checks across all result DataFrames
# =============================================================================
def validate_results(
    t1: pd.DataFrame,
    t2: pd.DataFrame,
    t3: pd.DataFrame,
    t4: pd.DataFrame,
    t5: pd.DataFrame,
) -> bool:
    """Verify all 5 query results pass basic consistency checks."""
    print("[ VALIDATE ] Sanity Checks")
    print("-" * 55)

    # Task 1: WHERE filtering -- only completed, positive, in-date-range rows
    assert (t1["annual_revenue"] > 0).all(), "T1: negative/zero revenue found"
    assert t1["transaction_count"].min() >= 1, "T1: customer with 0 transactions"
    print("  [OK] Task 1 -- WHERE: annual_revenue > 0, counts >= 1")

    # Task 2: GROUP BY -- multi-dimension check
    assert set(t2["customer_type"].unique()).issubset({"Enterprise", "SMB", "Startup"}), \
        "T2: unexpected customer_type value"
    assert (t2["monthly_revenue"] > 0).all(), "T2: month with zero revenue"
    assert (t2["unique_customers"] > 0).all(), "T2: month with zero unique customers"
    print("  [OK] Task 2 -- GROUP BY: valid types, revenue > 0, customers > 0")

    # Task 3: HAVING -- every returned customer meets both thresholds
    assert (t3["annual_revenue"] > 10_000).all(), "T3: HAVING threshold breached"
    assert (t3["transaction_count"] >= 5).all(),  "T3: count threshold breached"
    print("  [OK] Task 3 -- HAVING: all rows satisfy > $10k AND >= 5 transactions")

    # Task 4: WHERE + HAVING -- revenue share must sum to ~100 %
    total_share = t4["revenue_share_pct"].sum()
    assert abs(total_share - 100.0) < 0.5, f"T4: revenue shares sum to {total_share:.1f}%"
    print(f"  [OK] Task 4 -- Combined: revenue shares sum to {total_share:.1f}% ≈ 100%")

    # Task 5: ORDER BY -- ranks start at 1, are ascending
    assert t5["revenue_rank"].min() == 1, "T5: rank does not start at 1"
    assert t5["total_revenue"].is_monotonic_decreasing, "T5: not sorted descending"
    print("  [OK] Task 5 -- ORDER BY: revenue_rank starts at 1, sorted DESC")

    print()
    print("  \u2713 All validations passed.")
    return True


# =============================================================================
# Main
# =============================================================================
def main() -> None:
    print("=" * 55)
    print("  CyberGuard -- SQL Filtering & Aggregation (2.39)")
    print("=" * 55)
    print()

    engine = create_engine(CONNECTION_STRING)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("[OK] Database connection verified\n")

    # Seed tables
    print("[ SETUP ] Seeding tables")
    print("-" * 55)
    seed_tables(engine)

    # ── Task 1 ──────────────────────────────────────────────────────────────
    print("[ TASK 1 ] WHERE Filtering -- Data Quality Before Grouping")
    print("-" * 55)
    t1 = task1_where_filtering(engine)
    _print_result("Filtered customers (2024, completed, amount>0)", t1)

    # ── Task 2 ──────────────────────────────────────────────────────────────
    print("[ TASK 2 ] GROUP BY and Aggregation (customer_type × month)")
    print("-" * 55)
    t2 = task2_groupby_aggregation(engine)
    _print_result("Monthly revenue by segment", t2)

    # ── Task 3 ──────────────────────────────────────────────────────────────
    print("[ TASK 3 ] HAVING Filtering -- Group-Level Thresholds")
    print("-" * 55)
    t3 = task3_having_filtering(engine)
    _print_result("High-value customers (>$10k, 5+ purchases)", t3)

    # ── Task 4 ──────────────────────────────────────────────────────────────
    print("[ TASK 4 ] WHERE + HAVING Combined")
    print("-" * 55)
    t4 = task4_where_having_combined(engine)
    _print_result("Segment report with revenue share %", t4)

    # ── Task 5 ──────────────────────────────────────────────────────────────
    print("[ TASK 5 ] ORDER BY Ranking -- Top Performers")
    print("-" * 55)
    t5 = task5_orderby_ranking(engine)
    _print_result("Ranked segments by revenue", t5)

    # ── Validate ────────────────────────────────────────────────────────────
    validate_results(t1, t2, t3, t4, t5)

    print("=" * 55)
    print("  All tasks complete.")
    print("  WHERE filters rows. HAVING filters groups.")
    print("  One pattern. Applied consistently. Correct results.")
    print("=" * 55)


if __name__ == "__main__":
    main()
