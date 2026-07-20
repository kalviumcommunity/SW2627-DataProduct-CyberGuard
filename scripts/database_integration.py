# -*- coding: utf-8 -*-
from __future__ import annotations

"""
database_integration.py
=======================
SQL Environment & Database Integration -- Assignment 2.37
CyberGuard Data Product

Demonstrates moving from local CSVs to a queryable SQL database as the
single source of truth for all analyses.

Tasks
-----
Task 1 -- Setup Database Connection
Task 2 -- Load Cleaned DataFrame as Table
Task 3 -- Validate Schema
Task 4 -- Query and Return Results
Task 5 -- Make Loading Repeatable (reusable function)
"""

import sys
import io

from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, inspect, text

# Force UTF-8 output so special characters print correctly on Windows
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ─────────────────────────────────────────────────────────────
#  Paths
# ─────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR  = BASE_DIR / "data" / "raw"
DB_PATH  = BASE_DIR / "data" / "cyberguard.db"

# Connection string -- SQLite, file-based, zero server setup.
# For PostgreSQL swap with:
#   postgresql://username:password@localhost:5432/cyberguard
CONNECTION_STRING = f"sqlite:///{DB_PATH}"


# =============================================================
# TASK 1 -- Setup Database Connection
# =============================================================
def setup_connection(connection_string: str = CONNECTION_STRING):
    """
    Create a SQLAlchemy engine and verify the connection.

    Parameters
    ----------
    connection_string : str
        SQLAlchemy-compatible connection URL.
        SQLite  --> sqlite:///path/to/file.db
        PgSQL   --> postgresql://user:password@host:5432/dbname

    Returns
    -------
    Engine
        A connected SQLAlchemy engine ready for queries.
    """
    engine = create_engine(connection_string)

    # Test that the connection is live
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    print("[OK] Database connection successful")
    print(f"     Backend : {engine.dialect.name}")
    print(f"     Database: {DB_PATH.name}\n")
    return engine


# =============================================================
# TASK 2 -- Load Cleaned DataFrame as Table
# =============================================================
def load_tables(engine) -> dict[str, pd.DataFrame]:
    """
    Read cleaned source CSVs and write them to the database.

    Tables created
    --------------
    auth_logs_clean   -- authentication event log (CyberGuard raw feed, cleaned)
    customers_cleaned -- customer segment data (SaaS tier/LTV data)

    Returns
    -------
    dict[str, DataFrame]
        Dictionary of {table_name: DataFrame} for downstream use.
    """
    # -- Auth logs -------------------------------------------------
    auth_df = pd.read_csv(RAW_DIR / "auth_logs.csv")
    auth_df["timestamp"] = pd.to_datetime(auth_df["timestamp"])
    # Drop fully-duplicate rows (cleaning step)
    auth_df = auth_df.drop_duplicates()

    auth_df.to_sql("auth_logs_clean", engine, if_exists="replace", index=False)
    auth_count = pd.read_sql(
        "SELECT COUNT(*) AS row_count FROM auth_logs_clean", engine
    ).iloc[0]["row_count"]
    print(f"[OK] Loaded auth_logs_clean     -- {int(auth_count):>5} rows")

    # -- Customer / segment data ------------------------------------
    seg_df = pd.read_csv(RAW_DIR / "segment_data.csv")
    seg_df = seg_df.drop_duplicates()

    seg_df.to_sql("customers_cleaned", engine, if_exists="replace", index=False)
    seg_count = pd.read_sql(
        "SELECT COUNT(*) AS row_count FROM customers_cleaned", engine
    ).iloc[0]["row_count"]
    print(f"[OK] Loaded customers_cleaned   -- {int(seg_count):>5} rows")

    # Verify both tables exist
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"\n     Tables in database: {tables}\n")

    return {"auth_logs_clean": auth_df, "customers_cleaned": seg_df}


# =============================================================
# TASK 3 -- Validate Schema
# =============================================================
def validate_schema(engine) -> None:
    """
    Inspect every loaded table and validate column names and data types.

    For each table we:
      - Print all columns with their SQLAlchemy types and nullable status
      - Cross-check expected columns against the actual schema
    """
    inspector = inspect(engine)

    # -- auth_logs_clean -------------------------------------------
    print("-" * 55)
    print("TABLE SCHEMA: auth_logs_clean")
    print("-" * 55)
    auth_cols = inspector.get_columns("auth_logs_clean")
    for col in auth_cols:
        nullable_flag = ""if col["nullable"] else "NOT NULL"
        print(f"  {col['name']:<20} {str(col['type']):<20} {nullable_flag}")

    expected_auth = {
        "timestamp":   "DATETIME",
        "username":    "TEXT",
        "ip_address":  "TEXT",
        "country":     "TEXT",
        "status":      "TEXT",
        "device_type": "TEXT",
    }
    print("\nDATATYPE VALIDATION -- auth_logs_clean:")
    for col_name, expected_type in expected_auth.items():
        matches = [c for c in auth_cols if c["name"] == col_name]
        if not matches:
            print(f"  [FAIL] {col_name}: COLUMN MISSING")
            continue
        actual = str(matches[0]["type"]).upper()
        status = "[OK]  " if expected_type in actual else "[~]   "
        print(f"  {status} {col_name:<20} expected={expected_type:<12} actual={actual}")

    # -- customers_cleaned ------------------------------------------
    print()
    print("-" * 55)
    print("TABLE SCHEMA: customers_cleaned")
    print("-" * 55)
    seg_cols = inspector.get_columns("customers_cleaned")
    for col in seg_cols:
        nullable_flag = "" if col["nullable"] else "NOT NULL"
        print(f"  {col['name']:<20} {str(col['type']):<20} {nullable_flag}")

    expected_seg = {
        "customer_id":    "INTEGER",
        "customer_type":  "TEXT",
        "lifetime_value": "FLOAT",
        "churn":          "INTEGER",
    }
    print("\nDATATYPE VALIDATION -- customers_cleaned:")
    for col_name, expected_type in expected_seg.items():
        matches = [c for c in seg_cols if c["name"] == col_name]
        if not matches:
            print(f"  [FAIL] {col_name}: COLUMN MISSING")
            continue
        actual = str(matches[0]["type"]).upper()
        status = "[OK]  " if expected_type in actual else "[~]   "
        print(f"  {status} {col_name:<20} expected={expected_type:<12} actual={actual}")

    print()


# =============================================================
# TASK 4 -- Query and Return Results
# =============================================================
def run_queries(engine) -> None:
    """
    Execute SQL queries from Python and return results as DataFrames.

    Queries demonstrated
    --------------------
    Q1  Simple filter   -- all failed authentication attempts (threat feed)
    Q2  Aggregation     -- login attempts by country and status (risk heatmap)
    Q3  Enterprise LTV  -- customers_cleaned filtered by tier
    Q4  Segment summary -- avg LTV and churn rate per customer type
    """
    # -- Q1: Simple SELECT with filter -------------------------------
    q1 = """
        SELECT timestamp, username, ip_address, country, device_type
        FROM   auth_logs_clean
        WHERE  status = 'Failed'
        ORDER  BY timestamp DESC
        LIMIT  10
    """
    failed_logins = pd.read_sql(q1, engine)
    print("-" * 55)
    print(f"Q1 -- Failed login attempts (sample, {len(failed_logins)} rows shown):")
    print("-" * 55)
    print(failed_logins.to_string(index=False))
    print()

    # -- Q2: GROUP BY aggregation ------------------------------------
    q2 = """
        SELECT
            country,
            status,
            COUNT(*) AS attempt_count
        FROM   auth_logs_clean
        GROUP  BY country, status
        ORDER  BY attempt_count DESC
        LIMIT  15
    """
    risk_heatmap = pd.read_sql(q2, engine)
    print("-" * 55)
    print("Q2 -- Login attempts by country x status (risk heatmap):")
    print("-" * 55)
    print(risk_heatmap.to_string(index=False))
    print()

    # -- Q3: Simple segment filter -----------------------------------
    q3 = "SELECT * FROM customers_cleaned WHERE customer_type = 'Enterprise'"
    enterprise = pd.read_sql(q3, engine)
    print("-" * 55)
    print(f"Q3 -- Enterprise customers retrieved: {len(enterprise)} rows")
    print("-" * 55)
    print(enterprise.head(5).to_string(index=False))
    print()

    # -- Q4: Aggregation -- segment summary --------------------------
    q4 = """
        SELECT
            customer_type,
            COUNT(*)                          AS count,
            ROUND(AVG(lifetime_value), 2)     AS avg_ltv,
            ROUND(AVG(churn) * 100, 1)        AS churn_rate_pct,
            ROUND(AVG(retention_days), 1)     AS avg_retention_days
        FROM   customers_cleaned
        GROUP  BY customer_type
        ORDER  BY avg_ltv DESC
    """
    summary = pd.read_sql(q4, engine)
    print("-" * 55)
    print("Q4 -- Summary by customer segment:")
    print("-" * 55)
    print(summary.to_string(index=False))
    print()


# =============================================================
# TASK 5 -- Make Loading Repeatable
# =============================================================
def load_cleaned_data_to_database(
    df: pd.DataFrame,
    table_name: str,
    database_path: str | Path = DB_PATH,
    if_exists: str = "replace",
):
    """
    Load a cleaned DataFrame into a SQLite database -- repeatable and validated.

    Parameters
    ----------
    df : pd.DataFrame
        The cleaned DataFrame to persist.
    table_name : str
        Target SQL table name.
    database_path : str | Path
        Path to the SQLite .db file.  Defaults to data/cyberguard.db.
    if_exists : str
        Behaviour if table already exists: 'replace' (default) or 'append'.

    Returns
    -------
    Engine
        The connected SQLAlchemy engine so callers can run follow-up queries.

    Example
    -------
    >>> engine = load_cleaned_data_to_database(df_clean, 'customers_cleaned')
    >>> results = pd.read_sql("SELECT * FROM customers_cleaned LIMIT 10", engine)
    """
    conn_str = f"sqlite:///{database_path}"
    engine = create_engine(conn_str)

    # -- Load -------------------------------------------------------
    df.to_sql(table_name, engine, if_exists=if_exists, index=False)

    # -- Validate row count -----------------------------------------
    count_df = pd.read_sql(
        f"SELECT COUNT(*) AS ct FROM {table_name}", engine  # noqa: S608
    )
    rows_loaded = int(count_df.iloc[0]["ct"])

    # -- Validate schema --------------------------------------------
    inspector = inspect(engine)
    cols = inspector.get_columns(table_name)
    col_names = [c["name"] for c in cols]

    print(f"[OK] Loaded {rows_loaded} rows to '{table_name}'")
    print(f"     Columns ({len(col_names)}): {col_names}")
    print(f"     Database: {database_path}\n")

    return engine


# =============================================================
# Main -- run all tasks in sequence
# =============================================================
def main() -> None:
    print("=" * 55)
    print("  CyberGuard -- SQL Database Integration")
    print("=" * 55)
    print()

    # -- Task 1 ----------------------------------------------------
    print("[ TASK 1 ] Setup Database Connection")
    engine = setup_connection()

    # -- Task 2 ----------------------------------------------------
    print("[ TASK 2 ] Load Cleaned DataFrames as Tables")
    tables = load_tables(engine)

    # -- Task 3 ----------------------------------------------------
    print("[ TASK 3 ] Validate Schema")
    validate_schema(engine)

    # -- Task 4 ----------------------------------------------------
    print("[ TASK 4 ] Query and Return Results")
    run_queries(engine)

    # -- Task 5 ----------------------------------------------------
    print("[ TASK 5 ] Repeatable Load Function")
    # Demonstrate reusable function with segment data
    seg_df = tables["customers_cleaned"]
    engine2 = load_cleaned_data_to_database(seg_df, "customers_cleaned")

    # Any analyst can now query directly -- single source of truth
    sample = pd.read_sql(
        "SELECT * FROM customers_cleaned LIMIT 5", engine2
    )
    print("  Sample rows via reloaded engine:")
    print(sample.to_string(index=False))
    print()

    print("=" * 55)
    print("  All tasks complete.")
    print(f"  Single source of truth: {DB_PATH}")
    print("=" * 55)


if __name__ == "__main__":
    main()
