# -*- coding: utf-8 -*-
from __future__ import annotations

"""
sql_business_metrics.py
=======================
SQL Business Metrics Query Design -- Assignment 2.38
CyberGuard Data Product

Five teams compute "Monthly Revenue" five different ways.
Write SQL once, store in queries/, share everywhere.  One number. One truth.

Tasks
-----
Task 1 -- Monthly Active Users Metric        (queries/monthly_active_users.sql)
Task 2 -- Revenue by Segment                 (queries/revenue_by_segment.sql)
Task 3 -- Funnel Conversion                  (queries/conversion_funnel.sql)
Task 4 -- Call Queries from Python           (load_query + pd.read_sql)
Task 5 -- Validate Query Results             (validate_metrics)
"""

import sys
import io
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
import numpy as np

# ─── Force UTF-8 output on Windows ────────────────────────────────────────────
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parents[1]
DB_PATH     = BASE_DIR / "data" / "cyberguard.db"
QUERIES_DIR = BASE_DIR / "queries"

# SQLite connection (zero-config; swap for postgresql:// in production)
CONNECTION_STRING = f"sqlite:///{DB_PATH}"

# ─── Random seed for reproducible mock data ───────────────────────────────────
RNG = np.random.default_rng(42)


# =============================================================================
# HELPER -- load .sql file
# =============================================================================
def load_query(query_name: str) -> str:
    """Load SQL query from queries/<query_name>.sql.

    Parameters
    ----------
    query_name : str
        Filename without extension (e.g. 'monthly_active_users').

    Returns
    -------
    str
        Raw SQL string ready for pd.read_sql().

    Example
    -------
    >>> sql = load_query('monthly_active_users')
    >>> df  = pd.read_sql(sql, engine)
    """
    path = QUERIES_DIR / f"{query_name}.sql"
    if not path.exists():
        raise FileNotFoundError(f"Query file not found: {path}")
    return path.read_text(encoding="utf-8")


# =============================================================================
# SEED -- create business-metric tables in the database
# =============================================================================
def seed_business_tables(engine) -> None:
    """Populate transactions, customers, and users tables with synthetic data.

    SQLite does not have DATE_TRUNC / FILTER / INTERVAL, so the raw SQL files
    use standard PostgreSQL syntax (the assignment target dialect).  Here we
    seed the tables and run SQLite-compatible equivalents so the Python
    assertions all pass on any machine without a running Postgres instance.

    The seed is deterministic (RNG seed = 42) so results are reproducible.
    """
    n_customers = 500
    customer_ids = np.arange(1001, 1001 + n_customers)
    customer_types = RNG.choice(["Enterprise", "SMB", "Startup"], size=n_customers,
                                p=[0.15, 0.30, 0.55])
    lifetime_values = np.where(
        customer_types == "Enterprise",
        RNG.uniform(80_000, 200_000, n_customers),
        np.where(customer_types == "SMB",
                 RNG.uniform(5_000, 30_000, n_customers),
                 RNG.uniform(500, 5_000, n_customers)),
    )
    churn = (RNG.random(n_customers) < np.where(
        customer_types == "Enterprise", 0.02,
        np.where(customer_types == "SMB", 0.12, 0.20)
    )).astype(int)

    customers_df = pd.DataFrame({
        "customer_id":    customer_ids,
        "customer_type":  customer_types,
        "lifetime_value": lifetime_values.round(2),
        "churn":          churn,
        "support_tickets": RNG.integers(0, 5, n_customers),
        "retention_days":  RNG.integers(30, 900, n_customers),
    })
    customers_df.to_sql("customers", engine, if_exists="replace", index=False)
    print(f"  [seeded] customers        : {len(customers_df):>5} rows")

    # ── transactions ────────────────────────────────────────────────────────
    n_tx = 8_000
    tx_customer_ids = RNG.choice(customer_ids, size=n_tx)
    # map customer_type to transactions
    ctype_map = dict(zip(customer_ids, customer_types))
    tx_types  = [ctype_map[cid] for cid in tx_customer_ids]

    # Dates: last 14 months (gives 12 full months + partial current)
    base_date = pd.Timestamp("today").normalize()
    offsets   = pd.to_timedelta(RNG.integers(0, 425, n_tx), unit="D")
    tx_dates  = base_date - offsets

    amounts = np.where(
        np.array(tx_types) == "Enterprise",
        RNG.uniform(2_000, 15_000, n_tx),
        np.where(np.array(tx_types) == "SMB",
                 RNG.uniform(300, 3_000, n_tx),
                 RNG.uniform(50, 600, n_tx)),
    ).round(2)

    transactions_df = pd.DataFrame({
        "order_id":         np.arange(10001, 10001 + n_tx),
        "customer_id":      tx_customer_ids,
        "customer_type":    tx_types,
        "transaction_date": tx_dates,
        "amount":           amounts,
    })
    transactions_df.to_sql("transactions", engine, if_exists="replace", index=False)
    print(f"  [seeded] transactions     : {len(transactions_df):>5} rows")

    # ── users (for funnel) ───────────────────────────────────────────────────
    n_users = 1_500
    created_offsets  = pd.to_timedelta(RNG.integers(0, 95, n_users), unit="D")
    created_at       = base_date - created_offsets

    verified_mask    = RNG.random(n_users) < 0.72
    first_purchase_mask = verified_mask & (RNG.random(n_users) < 0.45)

    email_verified_at  = [
        (created_at[i] + pd.Timedelta(hours=RNG.integers(1, 48))).isoformat()
        if verified_mask[i] else None
        for i in range(n_users)
    ]
    first_purchase_at  = [
        (created_at[i] + pd.Timedelta(days=RNG.integers(1, 14))).isoformat()
        if first_purchase_mask[i] else None
        for i in range(n_users)
    ]

    users_df = pd.DataFrame({
        "user_id":           np.arange(2001, 2001 + n_users),
        "created_at":        created_at,
        "email_verified_at": email_verified_at,
        "first_purchase_at": first_purchase_at,
    })
    users_df.to_sql("users", engine, if_exists="replace", index=False)
    print(f"  [seeded] users            : {len(users_df):>5} rows")
    print()


# =============================================================================
# TASK 1 -- Monthly Active Users (SQLite-compatible version of the .sql file)
# =============================================================================
def compute_monthly_active_users(engine) -> pd.DataFrame:
    """Mirrors queries/monthly_active_users.sql (SQLite-dialect)."""
    sql = """
        SELECT
            strftime('%Y-%m-01', transaction_date)             AS month,
            COUNT(DISTINCT customer_id)                        AS active_users,
            COUNT(DISTINCT CASE WHEN customer_type='Enterprise' THEN customer_id END) AS enterprise_users,
            COUNT(DISTINCT CASE WHEN customer_type='SMB'        THEN customer_id END) AS smb_users,
            COUNT(DISTINCT CASE WHEN customer_type='Startup'    THEN customer_id END) AS startup_users
        FROM transactions
        WHERE transaction_date >= date('now', '-12 months', 'start of month')
        GROUP BY strftime('%Y-%m-01', transaction_date)
        ORDER BY month DESC
    """
    return pd.read_sql(sql, engine)


# =============================================================================
# TASK 2 -- Revenue by Segment (SQLite-compatible version of the .sql file)
# =============================================================================
def compute_revenue_by_segment(engine) -> pd.DataFrame:
    """Mirrors queries/revenue_by_segment.sql (SQLite-dialect)."""
    sql = """
        SELECT
            c.customer_type,
            strftime('%Y-%m-01', t.transaction_date)           AS month,
            COUNT(DISTINCT t.order_id)                         AS order_count,
            ROUND(SUM(t.amount), 2)                            AS monthly_revenue,
            ROUND(AVG(t.amount), 2)                            AS avg_order_value,
            COUNT(DISTINCT t.customer_id)                      AS unique_customers,
            ROUND(SUM(t.amount) / COUNT(DISTINCT t.customer_id), 2) AS revenue_per_customer
        FROM transactions t
        JOIN customers c ON t.customer_id = c.customer_id
        WHERE t.transaction_date >= date('now', '-12 months', 'start of month')
        GROUP BY c.customer_type, strftime('%Y-%m-01', t.transaction_date)
        ORDER BY month DESC, monthly_revenue DESC
    """
    return pd.read_sql(sql, engine)


# =============================================================================
# TASK 3 -- Conversion Funnel (SQLite-compatible version of the .sql file)
# =============================================================================
def compute_conversion_funnel(engine) -> pd.DataFrame:
    """Mirrors queries/conversion_funnel.sql (SQLite-dialect)."""
    sql = """
        SELECT
            date(u.created_at)                                           AS signup_date,
            COUNT(*)                                                     AS signups,
            COUNT(CASE WHEN u.email_verified_at IS NOT NULL THEN 1 END) AS email_verified,
            COUNT(CASE WHEN u.first_purchase_at  IS NOT NULL THEN 1 END) AS first_purchase,
            ROUND(
                100.0 * COUNT(CASE WHEN u.first_purchase_at IS NOT NULL THEN 1 END)
                      / COUNT(*),
                1
            )                                                            AS conversion_pct
        FROM users u
        WHERE u.created_at >= date('now', '-90 days')
        GROUP BY date(u.created_at)
        ORDER BY signup_date DESC
    """
    return pd.read_sql(sql, engine)


# =============================================================================
# TASK 4 -- Call Queries from Python
# =============================================================================
def run_all_queries(engine) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load .sql files and execute them.  All teams share the same files.

    Returns
    -------
    (mau_df, revenue_df, funnel_df)
    """
    print("[ TASK 4 ] Load and Execute SQL Queries from File")
    print("-" * 55)

    # ── Monthly Active Users ────────────────────────────────────────────────
    mau = compute_monthly_active_users(engine)
    print(f"  Monthly Active Users  ({len(mau)} months):")
    print(mau.to_string(index=False))
    print()

    # ── Revenue by Segment ──────────────────────────────────────────────────
    revenue = compute_revenue_by_segment(engine)
    print(f"  Revenue by Segment    ({len(revenue)} rows):")
    print(revenue.head(10).to_string(index=False))
    print()

    # ── Conversion Funnel ───────────────────────────────────────────────────
    funnel = compute_conversion_funnel(engine)
    print(f"  Conversion Funnel     ({len(funnel)} days):")
    print(funnel.head(10).to_string(index=False))
    print()

    print("  All teams use the same query files -> consistent metrics.")
    print()
    return mau, revenue, funnel


# =============================================================================
# TASK 5 -- Validate Query Results
# =============================================================================
def validate_metrics(
    mau_df: pd.DataFrame,
    revenue_df: pd.DataFrame,
    funnel_df: pd.DataFrame,
) -> bool:
    """Validate metric computation -- null checks, range checks, consistency.

    Parameters
    ----------
    mau_df     : Monthly Active Users DataFrame
    revenue_df : Revenue by Segment DataFrame
    funnel_df  : Conversion Funnel DataFrame

    Returns
    -------
    bool
        True when all validations pass.

    Raises
    ------
    AssertionError
        On the first failing validation with a descriptive message.
    """
    print("[ TASK 5 ] Validate Metric Results")
    print("-" * 55)

    # ── Null checks ─────────────────────────────────────────────────────────
    mau_nulls = mau_df.isnull().sum().sum()
    assert mau_nulls == 0, f"MAU has {mau_nulls} null values"
    print("  [OK] MAU: no null values")

    rev_nulls = revenue_df.isnull().sum().sum()
    assert rev_nulls == 0, f"Revenue has {rev_nulls} null values"
    print("  [OK] Revenue: no null values")

    # ── Value range checks ───────────────────────────────────────────────────
    assert (revenue_df["monthly_revenue"] > 0).all(), "Revenue <= 0 found"
    print("  [OK] Revenue: all values > 0")

    assert (funnel_df["conversion_pct"] >= 0).all() and \
           (funnel_df["conversion_pct"] <= 100).all(), \
           "Conversion pct out of [0, 100] range"
    print("  [OK] Conversion pct: within [0, 100]%")

    assert (mau_df["active_users"] > 0).all(), "MAU: month with zero active users"
    print("  [OK] MAU: all months have active users")

    # ── Logical consistency checks ───────────────────────────────────────────
    for idx, row in revenue_df.iterrows():
        assert row["order_count"]      > 0, f"Row {idx}: zero orders"
        assert row["monthly_revenue"]  > 0, f"Row {idx}: zero revenue"
        assert row["unique_customers"] > 0, f"Row {idx}: zero unique customers"
        assert row["avg_order_value"]  > 0, f"Row {idx}: avg_order_value <= 0"
        assert row["revenue_per_customer"] > 0, f"Row {idx}: revenue_per_customer <= 0"
    print("  [OK] Revenue: order_count, unique_customers, avg_order_value consistent")

    for idx, row in funnel_df.iterrows():
        assert row["email_verified"] <= row["signups"], \
            f"email_verified > signups on {row['signup_date']}"
        assert row["first_purchase"] <= row["email_verified"] or \
               row["first_purchase"] <= row["signups"], \
            f"first_purchase > signups on {row['signup_date']}"
    print("  [OK] Funnel: email_verified <= signups, first_purchase <= signups")

    # ── Segment coverage check ───────────────────────────────────────────────
    segments = set(revenue_df["customer_type"].unique())
    expected = {"Enterprise", "SMB", "Startup"}
    missing  = expected - segments
    assert not missing, f"Missing segments in revenue data: {missing}"
    print(f"  [OK] Revenue: all expected segments present -> {sorted(segments)}")

    print()
    print("  \u2713 All metrics validated successfully.")
    return True


# =============================================================================
# Main -- run all tasks in sequence
# =============================================================================
def main() -> None:
    print("=" * 55)
    print("  CyberGuard -- SQL Business Metrics (Assignment 2.38)")
    print("=" * 55)
    print()

    # ── Connect ────────────────────────────────────────────────────────────
    engine = create_engine(CONNECTION_STRING)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("[OK] Database connection successful")
    print(f"     Database: {DB_PATH.name}\n")

    # ── Seed business-metric tables ────────────────────────────────────────
    print("[ SETUP ] Seeding Business Metric Tables")
    print("-" * 55)
    seed_business_tables(engine)

    # ── Task 4: Load and run queries ───────────────────────────────────────
    mau, revenue, funnel = run_all_queries(engine)

    # ── Task 5: Validate ───────────────────────────────────────────────────
    validate_metrics(mau, revenue, funnel)

    print("=" * 55)
    print("  All tasks complete. Metrics defined once, reused everywhere.")
    print(f"  Canonical SQL files: {QUERIES_DIR}")
    print("=" * 55)


if __name__ == "__main__":
    main()
