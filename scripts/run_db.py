"""
CyberGuard SQLite Database Ingestion & Verification Script
"""
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cyberguard.etl.pipeline import ETLPipeline
from cyberguard.analytics.threat_rules import ThreatRuleEngine
from cyberguard.models.anomaly_engine import AnomalyEngine
from cyberguard.risk.risk_engine import RiskEngine
from cyberguard.sql.db_manager import DatabaseManager

def main():
    print("Executing End-to-End CyberGuard Pipeline for Database Ingestion...")
    # 1. ETL & Feature Engineering
    pipeline = ETLPipeline()
    raw_df, _ = pipeline.run()
    
    # 2. Rule-based Threat Evaluation
    threat_engine = ThreatRuleEngine()
    df_threats = threat_engine.evaluate_dataframe(raw_df)
    
    # 3. ML Anomaly Engine
    anomaly_engine = AnomalyEngine()
    df_anom = anomaly_engine.fit_predict(df_threats)
    
    # 4. Composite Risk Engine
    risk_engine = RiskEngine()
    final_df = risk_engine.evaluate_dataframe(df_anom)
    
    # 5. Ingest into SQLite Database
    db_mgr = DatabaseManager()
    db_mgr.ingest_events(final_df)
    
    res = db_mgr.execute_query("SELECT COUNT(*) as event_count FROM auth_events;")
    print(f"Database Ingestion Successful. Total auth_events in SQLite: {res.loc[0, 'event_count']}")

if __name__ == "__main__":
    main()
