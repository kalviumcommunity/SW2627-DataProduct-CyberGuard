import os
import sqlite3
import pandas as pd
import numpy as np
import logging
from datetime import datetime
from dotenv import load_dotenv

# 1. Load Environment Variables & Configuration
load_dotenv()

DATABASE_PATH = os.getenv("DATABASE_PATH", "data/cyberguard.db")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = "logs/pipeline.log"

# Create logs and data directories if they don't exist
os.makedirs("logs", exist_ok=True)
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

# 2. Setup Logging
numeric_level = getattr(logging, LOG_LEVEL, logging.INFO)
logging.basicConfig(
    level=numeric_level,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# 3. Main Functions

def ingest_data(filepath):
    """
    Ingest raw authentication logs from a CSV file.
    
    Args:
        filepath (str): Path to the raw logs CSV file.
        
    Returns:
        pd.DataFrame: Raw log DataFrame.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
    """
    logging.info(f"Starting data ingestion from {filepath}...")
    try:
        df = pd.read_csv(filepath)
        logging.info(f"Successfully ingested {len(df)} rows from {filepath}")
        return df
    except FileNotFoundError as e:
        logging.error(f"Ingestion failed: File not found at {filepath}")
        raise e
    except Exception as e:
        logging.error(f"Error during ingestion: {str(e)}")
        raise e

def process_data(df):
    """
    Process raw logs to calculate security risk scores.
    
    Heuristics applied:
    - Base risk = 10.
    - If login status is 'Failed', add 30.
    - If user is sensitive ('admin', 'root', 'db_backup') and status is 'Failed', add 20.
    - If login country is suspicious ('RU', 'CN', 'KP', 'IR'), add 15.
    - Detect Brute Force: If an IP has > 5 failed logins within the dataset, add 25 to all attempts from that IP.
    - Detect Travel Anomaly: If a user has logged in from multiple countries, add 20 to all logins.
    
    Risk scores are capped between 0 and 100.
    
    Args:
        df (pd.DataFrame): Raw log DataFrame with columns:
            - timestamp (str/datetime)
            - username (str)
            - ip_address (str)
            - country (str)
            - status (str)
            - device_type (str)
            
    Returns:
        pd.DataFrame: Transformed DataFrame including a 'risk_score' column.
    """
    logging.info("Starting behavioral analysis and risk scoring...")
    
    if df.empty:
        logging.warning("Empty DataFrame passed to process_data.")
        df['risk_score'] = []
        return df

    # Create a copy to prevent SettingWithCopyWarning
    processed_df = df.copy()
    processed_df['timestamp'] = pd.to_datetime(processed_df['timestamp'])
    
    # Initialize base risk
    processed_df['risk_score'] = 10.0
    
    # 1. Failed logins penalty
    processed_df.loc[processed_df['status'] == 'Failed', 'risk_score'] += 30
    
    # 2. Sensitive account failures
    sensitive_users = ['admin', 'root', 'db_backup']
    sensitive_failure_mask = (processed_df['status'] == 'Failed') & (processed_df['username'].isin(sensitive_users))
    processed_df.loc[sensitive_failure_mask, 'risk_score'] += 20
    
    # 3. Suspicious country access
    suspicious_countries = ['RU', 'CN', 'KP', 'IR']
    processed_df.loc[processed_df['country'].isin(suspicious_countries), 'risk_score'] += 15
    
    # 4. Brute force detection (aggregate fails per IP)
    failed_counts_by_ip = processed_df[processed_df['status'] == 'Failed'].groupby('ip_address').size()
    brute_force_ips = failed_counts_by_ip[failed_counts_by_ip > 5].index
    processed_df.loc[processed_df['ip_address'].isin(brute_force_ips), 'risk_score'] += 25
    
    # 5. Impossible Travel Anomaly (User logging in from multiple countries)
    user_country_counts = processed_df.groupby('username')['country'].nunique()
    travel_anomaly_users = user_country_counts[user_country_counts > 1].index
    processed_df.loc[processed_df['username'].isin(travel_anomaly_users), 'risk_score'] += 20
    
    # Cap risk score between 0 and 100
    processed_df['risk_score'] = np.clip(processed_df['risk_score'], 0, 100)
    
    # Convert timestamp back to string for database compatibility
    processed_df['timestamp'] = processed_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    logging.info(f"Processed {len(processed_df)} logs. High risk events (Score >= 70): {len(processed_df[processed_df['risk_score'] >= 70])}")
    return processed_df

def output_results(df, db_path):
    """
    Persist processed logs and aggregate risk profiles in a SQLite database.
    
    Args:
        df (pd.DataFrame): Processed DataFrame with risk scores.
        db_path (str): Filepath to the SQLite database.
    """
    logging.info(f"Persisting results to SQLite database at {db_path}...")
    
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Create table for individual auth events
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auth_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                username TEXT,
                ip_address TEXT,
                country TEXT,
                status TEXT,
                device_type TEXT,
                risk_score REAL
            )
        """)
        
        # 2. Create table for aggregated user risk scores
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_risk_profiles (
                username TEXT PRIMARY KEY,
                total_logins INTEGER,
                failed_logins INTEGER,
                max_risk_score REAL,
                avg_risk_score REAL,
                last_updated TEXT
            )
        """)
        
        conn.commit()
        
        # Insert events (replace table contents or append; we will replace for simple runs)
        # In a real environment, we'd append or insert unique events.
        df.to_sql("auth_events", conn, if_exists="replace", index=False)
        logging.info(f"Inserted {len(df)} records into auth_events table.")
        
        # Calculate and update user risk profiles
        profiles_df = df.groupby('username').agg(
            total_logins=('status', 'count'),
            failed_logins=('status', lambda x: int((x == 'Failed').sum())),
            max_risk_score=('risk_score', 'max'),
            avg_risk_score=('risk_score', 'mean')
        ).reset_index()
        
        profiles_df['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        profiles_df.to_sql("user_risk_profiles", conn, if_exists="replace", index=False)
        logging.info(f"Calculated and saved {len(profiles_df)} user risk profiles.")
        
        conn.commit()
        print(f"SUCCESS: Pipeline run completed. Database updated at: {db_path}")
        
    except sqlite3.Error as e:
        logging.error(f"Database error: {str(e)}")
        raise e
    finally:
        if conn:
            conn.close()
            logging.info("Database connection closed.")

# 4. Main Execution
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="CyberGuard SOC Logs Processing Pipeline")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/raw/auth_logs.csv", 
        help="Path to raw logs CSV"
    )
    args = parser.parse_args()
    
    try:
        logging.info("=== Starting CyberGuard Pipeline Execution ===")
        raw_data = ingest_data(args.input)
        processed_data = process_data(raw_data)
        output_results(processed_data, DATABASE_PATH)
        logging.info("=== Pipeline Execution Finished Successfully ===")
    except Exception as e:
        logging.error(f"Fatal error in pipeline: {str(e)}")
        print(f"ERROR: Pipeline failed. See {LOG_FILE} for details.")
        exit(1)
