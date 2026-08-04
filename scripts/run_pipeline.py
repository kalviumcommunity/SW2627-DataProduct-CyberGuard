"""
CyberGuard ETL Pipeline Entrypoint Script
"""
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cyberguard.etl.pipeline import ETLPipeline
from cyberguard.analytics.threat_rules import ThreatRuleEngine
from cyberguard.models.anomaly_engine import AnomalyEngine
from cyberguard.risk.risk_engine import RiskEngine

def main():
    print("Executing CyberGuard End-to-End Pipeline...")
    pipeline = ETLPipeline()
    raw_df, report = pipeline.run()
    
    threat_engine = ThreatRuleEngine()
    df_threats = threat_engine.evaluate_dataframe(raw_df)
    
    anomaly_engine = AnomalyEngine()
    df_anom = anomaly_engine.fit_predict(df_threats)
    
    risk_engine = RiskEngine()
    final_df = risk_engine.evaluate_dataframe(df_anom)
    
    print(f"Pipeline executed successfully. Total events processed: {len(final_df)}")
    print(f"High risk alerts identified: {len(final_df[final_df['risk_score'] >= 70])}")

if __name__ == "__main__":
    main()
