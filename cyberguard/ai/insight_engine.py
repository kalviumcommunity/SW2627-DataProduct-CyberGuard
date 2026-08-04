"""
AI & Natural Language Security Insight Generation Engine
"""
import pandas as pd
from typing import List, Dict, Any
from cyberguard.utils.logger import get_logger

logger = get_logger("insight_engine")

class AIInsightEngine:
    """Generates natural language security summaries and executive briefing cards."""

    @staticmethod
    def generate_narrative_insights(df: pd.DataFrame) -> List[str]:
        """Analyze dataset patterns and generate human-readable security bullet insights."""
        insights = []
        
        # 1. Total event & alert summary
        total_events = len(df)
        high_risk_df = df[df["risk_score"] >= 70]
        critical_count = len(df[df["severity"] == "CRITICAL"])
        high_count = len(df[df["severity"] == "HIGH"])
        
        insights.append(
            f"Analyzed **{total_events:,}** authentication events. Identified **{len(high_risk_df):,}** high-risk incidents "
            f"({critical_count} CRITICAL, {high_count} HIGH)."
        )

        # 2. Brute Force Analysis
        brute_events = df[df.get("flag_brute_force", False) == True]
        if not brute_events.empty:
            top_brute_user = brute_events["username"].mode()[0]
            top_brute_ip = brute_events["ip_address"].mode()[0]
            count = len(brute_events)
            insights.append(
                f"**Brute Force Burst Detected**: User `{top_brute_user}` experienced {count} rapid failed logins "
                f"originating from suspicious IP address `{top_brute_ip}`."
            )

        # 3. Impossible Travel Analysis
        travel_events = df[df.get("flag_impossible_travel", False) == True]
        if not travel_events.empty:
            for idx, row in travel_events.iterrows():
                user = row["username"]
                prev_country = row.get("prev_country", "Unknown")
                curr_country = row.get("country", "Unknown")
                speed = row.get("geo_speed_kmh", 0)
                insights.append(
                    f"**Impossible Travel Velocity Anomaly**: Account `{user}` authenticated from `{prev_country}` "
                    f"and then `{curr_country}` within a short window, travelling at an impossible velocity of **{speed:.0f} km/h**."
                )

        # 4. Credential Stuffing Analysis
        stuff_events = df[df.get("flag_credential_stuffing", False) == True]
        if not stuff_events.empty:
            ip = stuff_events["ip_address"].mode()[0]
            user_count = stuff_events["ip_distinct_users_10m"].max()
            insights.append(
                f"**Credential Stuffing Vector**: Malicious source IP `{ip}` targeted **{user_count} distinct user accounts** "
                f"in a automated credential spray attempt."
            )

        # 5. Privilege Escalation
        priv_events = df[df.get("flag_privilege_escalation", False) == True]
        if not priv_events.empty:
            targets = ", ".join(priv_events["username"].unique())
            insights.append(
                f"**Privilege Escalation Activity**: Flagged repeated unauthorized authentication attempts targeting "
                f"administrative accounts (`{targets}`)."
            )

        # 6. Overall Security Posture Verdict
        if len(high_risk_df) > 10:
            insights.append("**Security Posture Verdict**: HIGH RISK ENVIRONMENT. Elevated automated attack activity observed. Immediate threat mitigation recommended.")
        else:
            insights.append("**Security Posture Verdict**: NORMAL OPERATIONAL BASELINE. Low anomaly frequency detected.")

        return insights

    @staticmethod
    def generate_executive_summary(df: pd.DataFrame) -> Dict[str, Any]:
        """Build executive summary dashboard metrics dictionary."""
        total = len(df)
        failures = (df["status"] == "Failed").sum()
        fail_rate = (failures / total * 100.0) if total > 0 else 0.0
        
        return {
            "total_authentications": total,
            "failed_authentications": int(failures),
            "failure_rate_percent": round(fail_rate, 2),
            "critical_alerts": int((df["severity"] == "CRITICAL").sum()),
            "high_alerts": int((df["severity"] == "HIGH").sum()),
            "medium_alerts": int((df["severity"] == "MEDIUM").sum()),
            "unique_users_impacted": int(df[df["risk_score"] >= 70]["username"].nunique()),
            "top_attacking_countries": df[df["status"] == "Failed"]["country"].value_counts().head(5).to_dict()
        }
