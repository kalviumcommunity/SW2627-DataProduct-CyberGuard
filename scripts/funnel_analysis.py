from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def build_stages() -> dict[str, int]:
    return {
        "Click Signup": 10_000,
        "Email Entered": 8_000,
        "Password Created": 6_000,
        "Email Verified": 5_000,
        "Payment Added": 4_000,
        "First Purchase": 2_000,
    }


def build_funnel_df(stages: dict[str, int]) -> pd.DataFrame:
    stage_names = list(stages.keys())
    stage_counts = list(stages.values())

    drop_off_rows = []
    for idx in range(len(stage_counts) - 1):
        users_before = stage_counts[idx]
        users_after = stage_counts[idx + 1]
        users_lost = users_before - users_after
        drop_rate = (users_lost / users_before) * 100
        completion_rate = (users_after / users_before) * 100

        drop_off_rows.append(
            {
                "from_stage": stage_names[idx],
                "to_stage": stage_names[idx + 1],
                "users_before": users_before,
                "users_after": users_after,
                "users_lost": users_lost,
                "completion_rate_pct": completion_rate,
                "drop_rate_pct": drop_rate,
                "completion_rate": f"{completion_rate:.1f}%",
                "drop_rate": f"{drop_rate:.1f}%",
            }
        )

    return pd.DataFrame(drop_off_rows)


def plot_funnel(stages: dict[str, int]) -> Path:
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899"]

    bars = ax.bar(stages.keys(), stages.values(), color=colors)
    ax.set_ylabel("Users", fontsize=12)
    ax.set_xlabel("Stage", fontsize=12)
    ax.set_title("Signup Funnel: Volume by Stage", fontsize=14)
    ax.set_ylim(0, max(stages.values()) * 1.15)
    plt.xticks(rotation=45, ha="right")

    for bar, count in zip(bars, stages.values(), strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            count,
            f"{count:,}",
            ha="center",
            va="bottom",
            fontweight="bold",
        )

    plt.tight_layout()
    chart_path = OUTPUT_DIR / "funnel_chart.png"
    plt.savefig(chart_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return chart_path


def calculate_business_impact(funnel_df: pd.DataFrame, revenue_per_customer: int = 100) -> pd.DataFrame:
    impact_rows = []
    for _, row in funnel_df.iterrows():
        revenue_lost = int(row["users_lost"] * revenue_per_customer)
        impact_rows.append(
            {
                "drop_point": f"{row['from_stage']} → {row['to_stage']}",
                "users_lost": int(row["users_lost"]),
                "revenue_impact": revenue_lost,
                "priority": "HIGH" if revenue_lost >= 100_000 else "MEDIUM",
            }
        )

    impact_df = pd.DataFrame(impact_rows)
    return impact_df.sort_values(["revenue_impact", "users_lost"], ascending=False).reset_index(drop=True)


def build_recommendation(funnel_df: pd.DataFrame, revenue_per_customer: int = 100) -> str:
    biggest_drop_idx = (
        funnel_df.sort_values(
            ["drop_rate_pct", "users_lost", "revenue_impact"],
            ascending=[False, False, False],
        ).index[0]
        if "revenue_impact" in funnel_df.columns
        else funnel_df.sort_values(["drop_rate_pct", "users_lost"], ascending=[False, False]).index[0]
    )
    highest_impact = funnel_df.loc[biggest_drop_idx]
    additional_conversions = int(highest_impact["users_lost"] * 0.1)

    return f"""FUNNEL OPTIMIZATION PRIORITY:

CRITICAL BOTTLENECK:
Stage: {highest_impact['from_stage']} → {highest_impact['to_stage']}
Users Lost: {highest_impact['users_lost']:,.0f}
Drop Rate: {highest_impact['drop_rate']}
Revenue Impact: ${highest_impact['users_lost'] * revenue_per_customer:,.0f}

ROOT CAUSE INVESTIGATION NEEDED:
- Is step unclear? (Poor UX)
- Is step too complex? (Too many fields)
- Is step optional? (Should be required)
- Is step timing wrong? (Too early/late in funnel)

RECOMMENDED ACTION:
1. A/B test simplified version of step
2. Monitor drop rate before/after
3. Estimate revenue recovery
4. Roll out to 100% if improvement > 5%

EXPECTED IMPACT:
If we improve {highest_impact['from_stage']} → {highest_impact['to_stage']} completion by 10%:
Additional conversions: {additional_conversions:,.0f}
Additional revenue: ${additional_conversions * revenue_per_customer:,.0f}
"""


def main() -> None:
    stages = build_stages()
    funnel_df = build_funnel_df(stages)
    impact_df = calculate_business_impact(funnel_df)
    funnel_df = funnel_df.assign(
        drop_point=funnel_df.apply(lambda row: f"{row['from_stage']} → {row['to_stage']}", axis=1)
    ).merge(impact_df[["drop_point", "revenue_impact"]], on="drop_point", how="left")
    chart_path = plot_funnel(stages)

    print("Stage counts:")
    print(pd.Series(stages))
    print()

    print("Drop-off analysis:")
    print(funnel_df.to_string(index=False))
    print()

    biggest_drop = funnel_df.sort_values(["drop_rate_pct", "users_lost"], ascending=[False, False]).iloc[0]
    print("Biggest leak by drop rate:")
    print(biggest_drop.to_string())
    print()

    print("Business impact:")
    print(impact_df.assign(revenue_impact=impact_df["revenue_impact"].map(lambda value: f"${value:,.0f}" )).to_string(index=False))
    print()

    print(build_recommendation(funnel_df))
    print(f"\nFunnel visualization saved to: {chart_path}")


if __name__ == "__main__":
    main()