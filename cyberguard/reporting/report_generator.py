"""
Automated Executive & Technical SOC Report Generator (PDF & CSV)
"""
import os
import pandas as pd
from pathlib import Path
from typing import Dict, Any
from cyberguard.config.settings import REPORTS_DIR
from cyberguard.utils.logger import get_logger

logger = get_logger("report_generator")

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

class SOCReportGenerator:
    """Generates enterprise-grade SOC Executive & Technical PDF & CSV Reports."""

    def __init__(self, output_dir: Path = REPORTS_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_csv(self, df: pd.DataFrame, filename: str = "cyberguard_threat_report.csv") -> Path:
        """Export filtered events to CSV."""
        filepath = self.output_dir / filename
        df.to_csv(filepath, index=False)
        logger.info(f"Exported CSV report to {filepath}")
        return filepath

    def generate_pdf_report(self, df: pd.DataFrame, filename: str = "cyberguard_executive_report.pdf") -> Path:
        """Generate polished SOC Executive & Technical Incident PDF Report."""
        filepath = self.output_dir / filename
        
        if not REPORTLAB_AVAILABLE:
            # Fallback text summary report if reportlab is not installed
            txt_path = self.output_dir / "cyberguard_executive_report.txt"
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write("=== CYBERGUARD SOC EXECUTIVE INCIDENT REPORT ===\n\n")
                f.write(f"Total Authentications Analyzed: {len(df)}\n")
                f.write(f"High Risk Incidents (Score >= 70): {len(df[df['risk_score']>=70])}\n")
                f.write(f"Critical Incidents: {len(df[df['severity']=='CRITICAL'])}\n\n")
                f.write("=== TOP CRITICAL INCIDENTS ===\n")
                high_df = df[df['risk_score']>=70].head(10)
                for idx, r in high_df.iterrows():
                    f.write(f"[{r['timestamp']}] User: {r['username']} | Risk: {r['risk_score']} | Reason: {r['primary_reason']}\n")
            logger.info(f"Reportlab unavailable. Saved text report to {txt_path}")
            return txt_path

        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=10
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#475569"),
            spaceAfter=15
        )
        h2_style = ParagraphStyle(
            "DocH2",
            parent=styles["Heading2"],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=12,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            "DocBody",
            parent=styles["BodyText"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#334155")
        )

        story = []

        # 1. Header & Title
        story.append(Paragraph("CyberGuard SOC Security Threat Briefing", title_style))
        story.append(Paragraph("Automated Enterprise Executive & Technical Incident Summary Report", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#0284c7"), spaceAfter=15))

        # 2. Executive Summary Metrics
        total_events = len(df)
        high_risk = len(df[df["risk_score"] >= 70])
        crit_count = len(df[df["severity"] == "CRITICAL"])
        fail_count = len(df[df["status"] == "Failed"])

        metrics_data = [
            ["Metric", "Value", "Status / Threshold"],
            ["Total Authentication Events", f"{total_events:,}", "Monitored Baseline"],
            ["Failed Authentication Attempts", f"{fail_count:,}", f"{round(fail_count/total_events*100, 1)}% Failure Rate"],
            ["High Risk Incidents (Score >= 70)", f"{high_risk:,}", "Immediate Review Required"],
            ["CRITICAL Severity Threats", f"{crit_count:,}", "Action Required"]
        ]
        
        t_metrics = Table(metrics_data, colWidths=[200, 120, 200])
        t_metrics.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#f8fafc"), colors.white]),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t_metrics)
        story.append(Spacer(1, 15))

        # 3. Top High Risk Threats Table
        story.append(Paragraph("High-Priority Threat Incidents (Top 10)", h2_style))
        high_df = df[df["risk_score"] >= 70].sort_values(by="risk_score", ascending=False).head(10)
        
        if not high_df.empty:
            table_data = [["Timestamp", "User", "IP", "Vector", "Risk Score", "Severity"]]
            for idx, r in high_df.iterrows():
                table_data.append([
                    str(r["timestamp"])[:19],
                    str(r["username"]),
                    str(r["ip_address"]),
                    str(r.get("threat_vector", "Anomaly"))[:20],
                    f"{r['risk_score']:.1f}",
                    str(r.get("severity", "HIGH"))
                ])
                
            t_threats = Table(table_data, colWidths=[110, 80, 90, 110, 65, 65])
            t_threats.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#b91c1c")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#fef2f2"), colors.white]),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#fca5a5")),
                ('PADDING', (0,0), (-1,-1), 5),
                ('FONTSIZE', (0,0), (-1,-1), 9)
            ]))
            story.append(t_threats)
        else:
            story.append(Paragraph("No critical or high-risk threats detected in current dataset.", body_style))

        story.append(Spacer(1, 15))

        # 4. Strategic Recommendations
        story.append(Paragraph("Recommended Strategic Remediation Actions", h2_style))
        recs = [
            "1. **Enforce Mandatory Step-Up MFA**: Enable hardware key / TOTP MFA for high-risk users.",
            "2. **Perimeter Firewall IP Blocking**: Automatically block external IPs generating credential stuffing activity.",
            "3. **Geographical Access Controls**: Apply conditional access rules restricting concurrent multi-country logins within 1 hour.",
            "4. **Administrative Account Hardening**: Restrict `root` and `admin` shell access to dedicated jumpboxes."
        ]
        for rec in recs:
            story.append(Paragraph(rec, body_style))
            story.append(Spacer(1, 4))

        doc.build(story)
        logger.info(f"Generated PDF Executive Report at {filepath}")
        return filepath
