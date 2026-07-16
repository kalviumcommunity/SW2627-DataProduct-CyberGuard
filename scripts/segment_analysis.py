"""Comparative user segmentation and behavioral analysis.

This script implements:
1. Synthetic customer dataset generation (LTV, Churn, Tickets, Retention).
2. Segment-level grouping and aggregation.
3. Summary stats table with ranks and readabilities.
4. Smart-normalized heatmap visualization (green for good, red for bad).
5. Performer identification and business-facing strategic report.
"""

from __future__ import annotations

import os
import sys
import io
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configure standard output to support UTF-8 on Windows environments
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Define directory structures
BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR = BASE_DIR / "output"

# Ensure all directories exist
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate_segmentation_data(seed: int = 42) -> Path:
    """
    Generate synthetic customer dataset with Enterprise, SMB, and Startup segments.
    
    Proportions:
    - Enterprise: 5% of base (~50 customers), high LTV ($150k), low churn (1%), low tickets (0.8), high retention (720 days).
    - SMB: 40% of base (~400 customers), medium LTV ($8k), high churn (12%), high tickets (2.6), low retention (280 days).
    - Startup: 55% of base (~550 customers), low LTV ($2k), moderate churn (8%), moderate tickets (1.9), moderate retention (360 days).
    """
    np.random.seed(seed)
    n_total = 1000
    n_ent = int(n_total * 0.05)
    n_smb = int(n_total * 0.40)
    n_str = n_total - n_ent - n_smb
    
    customers = []
    
    # Helper to generate blocks
    def generate_block(start_id, n_rows, segment_name, mean_ltv, std_ltv, churn_rate, mean_tickets, mean_retention):
        # Churn: binary array matching churn rate exactly
        churn_count = int(round(n_rows * churn_rate))
        churn = np.zeros(n_rows, dtype=int)
        if churn_count > 0:
            churn_idx = np.random.choice(np.arange(n_rows), size=churn_count, replace=False)
            churn[churn_idx] = 1
            
        # LTV: lognormal or normal distribution
        ltv = np.random.normal(loc=mean_ltv, scale=std_ltv, size=n_rows)
        # Ensure LTV doesn't drop below a minimum threshold
        ltv = np.clip(ltv, mean_ltv * 0.5, None)
        
        # Support tickets: Poisson distribution
        tickets = np.random.poisson(lam=mean_tickets, size=n_rows)
        
        # Retention: Normal distribution
        retention = np.random.normal(loc=mean_retention, scale=mean_retention * 0.15, size=n_rows)
        retention = np.clip(retention, 30, None).astype(int)
        
        for i in range(n_rows):
            customers.append({
                "customer_id": start_id + i,
                "customer_type": segment_name,
                "lifetime_value": round(ltv[i], 2),
                "churn": churn[i],
                "support_tickets": tickets[i],
                "retention_days": retention[i]
            })
            
    generate_block(1001, n_ent, "Enterprise", 150000.0, 15000.0, 0.01, 0.8, 720.0)
    generate_block(1001 + n_ent, n_smb, "SMB", 8000.0, 1000.0, 0.12, 2.6, 280.0)
    generate_block(1001 + n_ent + n_smb, n_str, "Startup", 2000.0, 300.0, 0.08, 1.9, 360.0)
    
    df = pd.DataFrame(customers)
    # Shuffle dataset to make it realistic
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)
    
    raw_path = RAW_DIR / "segment_data.csv"
    df.to_csv(raw_path, index=False)
    print(f"[OK] Generated raw segmentation dataset at: {raw_path}")
    print(f"  Shape: {df.shape[0]} rows × {df.shape[1]} columns")
    return raw_path


def load_and_preprocess(raw_path: Path) -> pd.DataFrame:
    """Load raw dataset and verify shape/integrity."""
    df = pd.read_csv(raw_path)
    # Check for missing values (if any) and clean
    df = df.dropna()
    processed_path = PROCESSED_DIR / "segment_data_processed.csv"
    df.to_csv(processed_path, index=False)
    print(f"[OK] Preprocessed dataset saved to: {processed_path}")
    return df


def task1_compute_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Task 1: Group by customer type and calculate average LTV, Churn, Support tickets, Retention days, and count.
    """
    print("\n--- Task 1: Defining Segments & Computing Metrics ---")
    segment_metrics = df.groupby('customer_type').agg({
        'lifetime_value': 'mean',
        'churn': 'mean',
        'support_tickets': 'mean',
        'retention_days': 'mean',
        'customer_id': 'count'
    })
    
    segment_metrics.columns = ['avg_ltv', 'churn_rate', 'avg_tickets', 'avg_retention', 'count']
    print(segment_metrics)
    return segment_metrics


def task2_summary_table(segment_metrics: pd.DataFrame) -> pd.DataFrame:
    """
    Task 2: Format metrics with readable labels and rankings.
    """
    print("\n--- Task 2: Summary Statistics Table and Rankings ---")
    segment_summary = segment_metrics.copy()
    
    # Calculate ranks
    # Rank LTV (descending: high LTV is rank 1)
    segment_summary['ltv_rank'] = segment_summary['avg_ltv'].rank(ascending=False).astype(int)
    # Rank Churn (ascending: low churn is rank 1)
    segment_summary['churn_rank'] = segment_summary['churn_rate'].rank(ascending=True).astype(int)
    
    # Display formatted version
    formatted_summary = pd.DataFrame(index=segment_summary.index)
    formatted_summary['Sample Count'] = segment_summary['count']
    formatted_summary['Avg LTV'] = segment_summary['avg_ltv'].apply(lambda x: f"${x:,.2f}")
    formatted_summary['LTV Rank'] = segment_summary['ltv_rank']
    formatted_summary['Churn Rate'] = segment_summary['churn_rate'].apply(lambda x: f"{x:.1%}")
    formatted_summary['Churn Rank'] = segment_summary['churn_rank']
    formatted_summary['Avg Tickets'] = segment_summary['avg_tickets'].round(2)
    formatted_summary['Avg Retention'] = segment_summary['avg_retention'].round(1).astype(str) + " days"
    
    print(formatted_summary)
    return segment_summary


def task3_visual_comparison(segment_metrics: pd.DataFrame) -> None:
    """
    Task 3: Create visual comparison heatmap with scale-normalizations.
    We normalize metrics so colors are readable (0=bad/red, 1=good/green):
    - LTV: high is green, low is red.
    - Churn Rate: low is green, high is red.
    - Avg Tickets: low is green, high is red.
    """
    print("\n--- Task 3: Visual Comparison Heatmap ---")
    
    # Extract core columns
    heatmap_data = segment_metrics[['avg_ltv', 'churn_rate', 'avg_tickets']].copy()
    
    # Normalize each column to [0, 1] range for visual colors where 1 is "good" and 0 is "bad"
    norm_data = pd.DataFrame(index=heatmap_data.index)
    
    # LTV: higher is better
    min_ltv, max_ltv = heatmap_data['avg_ltv'].min(), heatmap_data['avg_ltv'].max()
    norm_data['LTV (Revenue)'] = (heatmap_data['avg_ltv'] - min_ltv) / (max_ltv - min_ltv)
    
    # Churn Rate: lower is better
    min_churn, max_churn = heatmap_data['churn_rate'].min(), heatmap_data['churn_rate'].max()
    norm_data['Churn Rate'] = (max_churn - heatmap_data['churn_rate']) / (max_churn - min_churn)
    
    # Support Tickets: lower is better
    min_tix, max_tix = heatmap_data['avg_tickets'].min(), heatmap_data['avg_tickets'].max()
    norm_data['Avg Tickets'] = (max_tix - heatmap_data['avg_tickets']) / (max_tix - min_tix)
    
    # Create text annotations using the original (non-normalized) metrics formatted nicely
    annotations = np.array([
        [f"${row['avg_ltv']:,.0f}", f"{row['churn_rate']:.1%}", f"{row['avg_tickets']:.2f}"]
        for _, row in heatmap_data.iterrows()
    ])
    
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
    
    sns.heatmap(
        norm_data,
        annot=annotations,
        fmt="",
        cmap="RdYlGn",
        cbar=True,
        cbar_kws={'label': 'Performance Index (Green = Good, Red = Bad)', 'ticks': [0, 1]},
        linewidths=1.5,
        linecolor="#f1f5f9",
        annot_kws={"size": 13, "weight": "bold"},
        ax=ax
    )
    
    ax.set_title("Customer Segment Comparative Heatmap", fontsize=15, fontweight="bold", pad=20)
    ax.set_xlabel("Operational Metrics", fontsize=12, labelpad=10)
    ax.set_ylabel("Customer Segment", fontsize=12, labelpad=10)
    ax.tick_params(labelsize=11)
    
    plt.tight_layout()
    
    # Save to both target output folder and root directory
    plot_path_output = OUTPUT_DIR / "segment_heatmap.png"
    plot_path_root = BASE_DIR / "segment_heatmap.png"
    
    plt.savefig(plot_path_output, facecolor="white", bbox_inches="tight")
    plt.savefig(plot_path_root, facecolor="white", bbox_inches="tight")
    plt.close()
    
    print(f"[OK] Saved segment heatmap to: {plot_path_output}")
    print(f"[OK] Saved segment heatmap copy to: {plot_path_root}")


def task4_performer_analysis(segment_metrics: pd.DataFrame) -> tuple[str, float, str, float]:
    """
    Task 4: Identify and document top and bottom performer segments.
    """
    print("\n--- Task 4: Top and Bottom Performer Analysis ---")
    
    top_segment = segment_metrics['avg_ltv'].idxmax()
    top_value = segment_metrics.loc[top_segment, 'avg_ltv']
    
    high_churn_segment = segment_metrics['churn_rate'].idxmax()
    high_churn_value = segment_metrics.loc[high_churn_segment, 'churn_rate']
    
    best_retention_segment = segment_metrics['avg_retention'].idxmax()
    best_retention_value = segment_metrics.loc[best_retention_segment, 'avg_retention']
    
    insights = f"""PERFORMER ANALYSIS METRICS:
- HIGHEST VALUE SEGMENT: {top_segment} (${top_value:,.2f} Average LTV)
- HIGHEST CHURN RISK: {high_churn_segment} ({high_churn_value:.1%} Churn Rate)
- BEST RETENTION RATE: {best_retention_segment} ({best_retention_value:.1f} Days Avg Lifespan)
"""
    print(insights)
    return top_segment, top_value, high_churn_segment, high_churn_value


def task5_business_insights(segment_metrics: pd.DataFrame, top_seg: str, top_val: float, bad_seg: str, bad_val: float) -> None:
    """
    Task 5: Connect data metrics to strategic recommendations and export the report.
    """
    print("\n--- Task 5: Business-Facing Insights & Action Plan ---")
    
    # Collect metric stats
    ent_row = segment_metrics.loc["Enterprise"]
    smb_row = segment_metrics.loc["SMB"]
    str_row = segment_metrics.loc["Startup"]
    
    report_text = f"""============================================================
CUSTOMER SEGMENTATION & OPERATIONAL STRATEGY REPORT
============================================================

1. EXECUTIVE SUMMARY & KEY PERFORMERS
------------------------------------------------------------
- Top Value Performer: {top_seg} with an average LTV of ${top_val:,.2f}.
- Critical Churn Threat: {bad_seg} with a high churn rate of {bad_val:.1%}.
- Customer Base Composition:
  * Enterprise: {ent_row['count']:.0f} accounts ({ent_row['count']/1000:.1%})
  * SMB: {smb_row['count']:.0f} accounts ({smb_row['count']/1000:.1%})
  * Startup: {str_row['count']:.0f} accounts ({str_row['count']/1000:.1%})

2. SEGMENT STRATEGY SUMMARY
------------------------------------------------------------

Enterprise (5.0% of base, ${ent_row['avg_ltv']:,.0f} LTV, {ent_row['churn_rate']:.1%} churn):
- Insight: This segment generates the highest value per customer and demonstrates near-perfect loyalty. Despite their small headcount, they represent the financial bedrock of the business.
- Strategic Recommendation: Maintain dedicated premium support, implement regular Executive Business Reviews (EBRs), and offer white-glove onboarding to safeguard these high-value accounts.

SMB (40.0% of base, ${smb_row['avg_ltv']:,.0f} LTV, {smb_row['churn_rate']:.1%} churn):
- Insight: This group constitutes a significant portion of our customer base but is severely plagued by a high 12% churn rate. Their high support ticket volume suggests ongoing operational friction.
- Strategic Recommendation: Re-engineer the onboarding experience, deploy automated in-app tutorials, and offer a lower-tier/cost-effective self-serve support system to reduce support costs and improve retention.

Startup (55.0% of base, ${str_row['avg_ltv']:,.0f} LTV, {str_row['churn_rate']:.1%} churn):
- Insight: Startups represent the majority of our customers, but they have the lowest individual economic value. Churn is moderate at 8%, showing some interest but budget sensitivity.
- Strategic Recommendation: Implement standard self-service resources, developer education portals, and automated email nurturing campaigns. Focus on scalable support options that do not consume manual engineering hours.

3. STRATEGIC METRICS MATRIX
------------------------------------------------------------
Segment      | Size | Avg LTV     | Churn Rate | Avg Tickets | Avg Retention
-------------|------|-------------|------------|-------------|--------------
Enterprise   | {ent_row['count']:<4.0f} | ${ent_row['avg_ltv']:<11,.0f} | {ent_row['churn_rate']:<10.1%} | {ent_row['avg_tickets']:<11.2f} | {ent_row['avg_retention']:.1f} days
SMB          | {smb_row['count']:<4.0f} | ${smb_row['avg_ltv']:<11,.0f} | {smb_row['churn_rate']:<10.1%} | {smb_row['avg_tickets']:<11.2f} | {smb_row['avg_retention']:.1f} days
Startup      | {str_row['count']:<4.0f} | ${str_row['avg_ltv']:<11,.0f} | {str_row['churn_rate']:<10.1%} | {str_row['avg_tickets']:<11.2f} | {str_row['avg_retention']:.1f} days

============================================================
Generated by Antigravity Segmentation Engine | {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    print(report_text)
    
    # Save report
    output_path = OUTPUT_DIR / "segment_analysis_report.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"[OK] Saved strategy report to: {output_path}")


def main():
    print("============================================================")
    print("STARTING BEHAVIOURAL ANALYSIS & SEGMENTATION WORKFLOW")
    print("============================================================")
    
    # Generate raw data
    raw_path = generate_segmentation_data()
    
    # Preprocess
    df = load_and_preprocess(raw_path)
    
    # Task 1: Compute metrics
    metrics = task1_compute_metrics(df)
    
    # Task 2: Rankings & Summary statistics table
    task2_summary_table(metrics)
    
    # Task 3: Visual heatmap comparison
    task3_visual_comparison(metrics)
    
    # Task 4: Performer analysis
    top_seg, top_val, bad_seg, bad_val = task4_performer_analysis(metrics)
    
    # Task 5: Business-facing strategic report
    task5_business_insights(metrics, top_seg, top_val, bad_seg, bad_val)
    
    print("\n============================================================")
    print("BEHAVIOURAL ANALYSIS WORKFLOW COMPLETED SUCCESSFULLY!")
    print("============================================================")


if __name__ == "__main__":
    main()
