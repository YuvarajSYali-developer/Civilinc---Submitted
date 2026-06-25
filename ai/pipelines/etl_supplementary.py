"""
CivilInc ETL Pipeline — Supplementary Datasets
================================================
Generates:
  1. budgets.csv          — Multi-year departmental budget data (2019–2024)
  2. citizen_feedback.csv — Complaint satisfaction feedback
  3. officer_workload.csv — Monthly officer performance metrics

Sources modeled on:
  - BBMP Annual Budget Reports 2019–2024
  - India OGD departmental expenditure patterns
  - Karnataka State Budget allocation norms
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import random
import json
from pathlib import Path

SEED = 42
np.random.seed(SEED)
random.seed(SEED)

OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DEPARTMENTS = {
    "ROADS": {"base_budget_cr": 500, "growth_rate": 0.08, "volatility": 0.12},
    "WATER": {"base_budget_cr": 350, "growth_rate": 0.06, "volatility": 0.10},
    "ELEC":  {"base_budget_cr": 200, "growth_rate": 0.07, "volatility": 0.09},
    "PARKS": {"base_budget_cr": 100, "growth_rate": 0.05, "volatility": 0.15},
    "BLDG":  {"base_budget_cr": 250, "growth_rate": 0.06, "volatility": 0.11},
    "SWM":   {"base_budget_cr": 150, "growth_rate": 0.09, "volatility": 0.10},
}

# Utilization patterns by dept (India govt depts typically under-utilize)
UTILIZATION_PATTERNS = {
    "ROADS": {"mean": 0.78, "std": 0.12},
    "WATER": {"mean": 0.82, "std": 0.09},
    "ELEC":  {"mean": 0.71, "std": 0.11},
    "PARKS": {"mean": 0.65, "std": 0.14},
    "BLDG":  {"mean": 0.74, "std": 0.13},
    "SWM":   {"mean": 0.85, "std": 0.08},
}

FEEDBACK_TEMPLATES = {
    "positive": [
        "Issue was resolved quickly. Very satisfied with the response.",
        "The officer came within 24 hours and fixed the problem. Good work BBMP.",
        "Excellent service. Pothole was repaired the next day itself.",
        "Water supply was restored. Thank the department for quick action.",
        "Very happy with the resolution. Keep it up.",
        "The streetlight was fixed promptly. Good coordination.",
        "Problem solved within the promised time. Happy with service.",
        "Quick response and proper repair done. 5 stars.",
    ],
    "neutral": [
        "Work done but took more time than expected.",
        "Issue resolved but the quality of repair could be better.",
        "Response was okay, not great. Could be faster.",
        "Problem fixed after multiple follow-ups. Should improve.",
        "Work completed but left a lot of mess behind.",
        "Service was average. Expected better from BBMP.",
        "Issue resolved eventually. Process needs to be streamlined.",
    ],
    "negative": [
        "Very poor service. Had to call multiple times before anyone came.",
        "The repair was done badly and the same problem recurred within a week.",
        "Absolutely no response for two weeks. Terrible service.",
        "Officers came but did not fix the root cause. Still facing the same issue.",
        "The complaint was closed without resolution. Very disappointed.",
        "Pathetic response time. This needs immediate improvement.",
        "No follow-up was done after marking as resolved. Issue still persists.",
        "Three weeks and still no action taken. Zero stars.",
    ],
}


# ─── Budget Dataset ───────────────────────────────────────────────────────────
def generate_budgets() -> pd.DataFrame:
    print("Generating budget dataset (2019–2024)...")
    records = []
    years = list(range(2019, 2025))

    for dept, cfg in DEPARTMENTS.items():
        prev_util = None
        prev_allocated = None

        for i, year in enumerate(years):
            # Budget grows with some noise
            growth = cfg["growth_rate"] + np.random.normal(0, 0.02)
            if prev_allocated is None:
                allocated = cfg["base_budget_cr"]
            else:
                allocated = prev_allocated * (1 + growth)

            # Add one-time project surges (Smart City injections)
            if year in [2021, 2023] and dept in ["ROADS", "WATER"]:
                allocated *= random.uniform(1.10, 1.25)

            allocated = round(allocated, 2)

            # Utilization
            util_cfg = UTILIZATION_PATTERNS[dept]
            util_pct = np.random.normal(util_cfg["mean"], util_cfg["std"])
            util_pct = max(0.40, min(0.99, util_pct))

            # COVID dip in 2020
            if year == 2020:
                util_pct *= random.uniform(0.65, 0.80)

            utilized = round(allocated * util_pct, 2)
            util_pct_final = round(util_pct * 100, 1)

            yoy_growth = round(((allocated / prev_allocated) - 1) * 100, 1) if prev_allocated else 0.0

            # Complaint and project counts (correlated with budget size)
            base_complaints = int(allocated * random.uniform(150, 250))
            base_projects = int(allocated * random.uniform(2, 5))

            records.append({
                "year": year,
                "department": dept,
                "allocated_crore": allocated,
                "utilized_crore": utilized,
                "utilization_pct": util_pct_final,
                "previous_year_utilized": round(prev_util, 2) if prev_util else None,
                "yoy_growth_pct": yoy_growth,
                "complaint_count": base_complaints,
                "project_count": base_projects,
                "carry_forward_crore": round(allocated - utilized, 2),
            })

            prev_util = utilized
            prev_allocated = allocated

    df = pd.DataFrame(records)
    return df


# ─── Citizen Feedback Dataset ─────────────────────────────────────────────────
def generate_feedback(n: int = 30000) -> pd.DataFrame:
    """
    Generates feedback records linked to the complaints dataset.
    ~65% of resolved complaints have feedback.
    """
    print(f"Generating {n:,} citizen feedback records...")
    records = []

    for i in range(1, n + 1):
        # Match complaint IDs from the complaints dataset
        # Resolved complaints are CMP-0000001 to ~CMP-0044000 range
        complaint_num = random.randint(1, 44000)
        complaint_id = f"CMP-{str(complaint_num).zfill(7)}"

        response_time = max(1, int(np.random.exponential(scale=5)))
        resolution_time = max(response_time, int(np.random.exponential(scale=10)))

        # Satisfaction inversely correlated with wait time
        if resolution_time <= 3:
            rating_weights = [0.02, 0.05, 0.13, 0.35, 0.45]
        elif resolution_time <= 7:
            rating_weights = [0.05, 0.10, 0.25, 0.35, 0.25]
        elif resolution_time <= 14:
            rating_weights = [0.10, 0.20, 0.30, 0.25, 0.15]
        else:
            rating_weights = [0.25, 0.30, 0.25, 0.12, 0.08]

        rating = random.choices([1, 2, 3, 4, 5], weights=rating_weights)[0]
        sentiment = "positive" if rating >= 4 else ("neutral" if rating == 3 else "negative")
        feedback_text = random.choice(FEEDBACK_TEMPLATES[sentiment])
        resolution_satisfactory = rating >= 3

        submitted_date = datetime(2022, 1, 1) + timedelta(
            days=random.randint(0, 1095),
            hours=random.randint(6, 22),
        )

        records.append({
            "feedback_id": f"FBK-{str(i).zfill(7)}",
            "complaint_id": complaint_id,
            "rating": rating,
            "sentiment": sentiment,
            "feedback_text": feedback_text,
            "response_time_days": response_time,
            "resolution_time_days": resolution_time,
            "resolution_satisfactory": resolution_satisfactory,
            "submitted_date": submitted_date.strftime("%Y-%m-%d %H:%M:%S"),
        })

    return pd.DataFrame(records)


# ─── Officer Workload Dataset ─────────────────────────────────────────────────
def generate_officer_workload(n_officers: int = 250) -> pd.DataFrame:
    """
    Monthly workload metrics per officer across 36 months (2022–2024).
    Derived from complaint + project distributions.
    """
    print(f"Generating workload dataset for {n_officers} officers × 36 months...")

    DEPT_OFFICER_MAP = {
        "ROADS": int(n_officers * 0.30),
        "WATER": int(n_officers * 0.25),
        "ELEC":  int(n_officers * 0.15),
        "PARKS": int(n_officers * 0.10),
        "BLDG":  int(n_officers * 0.12),
        "SWM":   int(n_officers * 0.08),
    }

    DEPT_SLA_HOURS = {"ROADS": 48, "WATER": 24, "ELEC": 12, "PARKS": 72, "BLDG": 96, "SWM": 24}
    DEPT_ROLES = {
        "ROADS": ["Executive Engineer", "Assistant Engineer", "Junior Engineer", "Coordinator"],
        "WATER": ["Executive Engineer", "Assistant Engineer", "Field Officer", "Coordinator"],
        "ELEC":  ["Executive Engineer", "Electrical Engineer", "Junior Engineer"],
        "PARKS": ["Horticulture Officer", "Assistant Engineer", "Supervisor"],
        "BLDG":  ["Town Planner", "Building Inspector", "Assistant Engineer"],
        "SWM":   ["Sanitary Inspector", "Field Officer", "Coordinator"],
    }

    months = pd.date_range("2022-01-01", "2024-12-01", freq="MS")
    records = []
    officer_counter = 1

    for dept, count in DEPT_OFFICER_MAP.items():
        sla_hours = DEPT_SLA_HOURS[dept]
        roles = DEPT_ROLES[dept]

        for o in range(count):
            officer_id = f"OFF-{str(officer_counter).zfill(4)}"
            role = random.choice(roles)
            base_capacity = random.randint(15, 45)  # complaints/month

            # Simulate officer skill (some officers consistently better)
            skill_factor = np.random.normal(1.0, 0.15)
            skill_factor = max(0.6, min(1.4, skill_factor))

            for month in months:
                # Seasonal variation (monsoon months = more complaints)
                seasonal = 1.0
                if month.month in [6, 7, 8, 9]:  # Bengaluru monsoon
                    seasonal = random.uniform(1.3, 1.8)

                assigned = int(base_capacity * seasonal * random.uniform(0.8, 1.2))
                resolved_rate = min(0.98, skill_factor * random.uniform(0.65, 0.95))
                resolved = int(assigned * resolved_rate)

                avg_res_days = max(0.5, np.random.normal(
                    sla_hours / 24 * (1.0 / skill_factor),
                    sla_hours / 48
                ))

                sla_breach_rate = max(0, 1 - skill_factor) * random.uniform(0.1, 0.4)
                sla_breaches = int(assigned * sla_breach_rate)

                projects = random.choices([0, 1, 2, 3, 4], weights=[0.30, 0.35, 0.20, 0.10, 0.05])[0]

                # Workload score: normalized 0–1
                normalized_assigned = min(1.0, assigned / 60)
                normalized_breach = min(1.0, sla_breach_rate)
                normalized_res_time = min(1.0, avg_res_days / (sla_hours / 12))
                workload_score = round(
                    (normalized_assigned * 0.4 + normalized_breach * 0.3 + normalized_res_time * 0.3),
                    3
                )
                workload_score = min(1.0, workload_score)

                records.append({
                    "officer_id": officer_id,
                    "department": dept,
                    "role": role,
                    "period": month.strftime("%Y-%m"),
                    "complaints_assigned": assigned,
                    "complaints_resolved": resolved,
                    "resolution_rate_pct": round(resolved_rate * 100, 1),
                    "avg_resolution_days": round(avg_res_days, 1),
                    "sla_breach_count": sla_breaches,
                    "sla_breach_rate_pct": round(sla_breach_rate * 100, 1),
                    "projects_managed": projects,
                    "workload_score": workload_score,
                    "skill_factor": round(skill_factor, 3),
                })

            officer_counter += 1

    return pd.DataFrame(records)


if __name__ == "__main__":
    # Budgets
    df_budgets = generate_budgets()
    df_budgets.to_csv(OUTPUT_DIR / "budgets.csv", index=False)
    print(f"✅ budgets.csv — {len(df_budgets)} records")
    print(f"   Years: {df_budgets['year'].min()}–{df_budgets['year'].max()}")
    print(f"   Depts: {df_budgets['department'].nunique()}")
    print(f"   Avg utilization: {df_budgets['utilization_pct'].mean():.1f}%")

    # Feedback
    df_feedback = generate_feedback(30000)
    df_feedback.to_csv(OUTPUT_DIR / "citizen_feedback.csv", index=False)
    print(f"\n✅ citizen_feedback.csv — {len(df_feedback):,} records")
    print(f"   Avg rating: {df_feedback['rating'].mean():.2f}/5")
    print(f"   Sentiment: {df_feedback['sentiment'].value_counts().to_dict()}")

    # Officer workload
    df_workload = generate_officer_workload(250)
    df_workload.to_csv(OUTPUT_DIR / "officer_workload.csv", index=False)
    print(f"\n✅ officer_workload.csv — {len(df_workload):,} records")
    print(f"   Officers: {df_workload['officer_id'].nunique()}")
    print(f"   Months: {df_workload['period'].nunique()}")
    print(f"   Avg workload score: {df_workload['workload_score'].mean():.3f}")
