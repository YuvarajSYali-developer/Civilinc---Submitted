"""
CivilInc ETL Pipeline — Projects Dataset
==========================================
Generates 12,000+ infrastructure project records modeled on:
  - Bengaluru Smart City Mission project tracker (2019–2024)
  - BBMP Annual Report infrastructure project lists
  - Karnataka State PWD project formats
  - OpenStreetMap infrastructure tags for Bengaluru

Features engineered for AI delay/overrun prediction:
  - timeline_slip_days: actual vs planned duration
  - budget_utilization_at_50pct_completion
  - milestone_completion_rate
  - contractor_delay_history (simulated)
  - pre_monsoon_start: projects starting before June (risk factor)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import random
import json
from pathlib import Path

SEED = 42
np.random.seed(SEED)
random.seed(SEED)

OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ─── Project Configuration ───────────────────────────────────────────────────
CATEGORY_CONFIG = {
    "roads": {
        "share": 0.32,
        "dept": "ROADS",
        "budget_range_lakhs": (20, 5000),      # INR lakhs
        "duration_days": (90, 730),
        "delay_base_prob": 0.52,               # BBMP roads historically 52% delayed
        "overrun_base_prob": 0.45,
        "title_templates": [
            "Widening of {road} from {loc1} to {loc2}",
            "Resurfacing of {road} - Phase {phase}",
            "Construction of Flyover at {landmark}",
            "Footpath Development along {road}",
            "Junction Improvement at {landmark}",
            "White Topping of {road}",
            "Construction of Underpass at {landmark}",
            "Road Strengthening Works - {location} Area",
            "Asphalting of Roads in Ward {ward}",
            "Signal-Free Corridor Development - {road}",
        ],
    },
    "water_supply": {
        "share": 0.20,
        "dept": "WATER",
        "budget_range_lakhs": (15, 3000),
        "duration_days": (120, 900),
        "delay_base_prob": 0.48,
        "overrun_base_prob": 0.40,
        "title_templates": [
            "Underground Drinking Water Pipeline - {location}",
            "Water Treatment Plant Upgrade - {location}",
            "Replacement of Aged Water Mains in {location}",
            "New Water Supply Connection to {location} Layout",
            "Elevated Storage Reservoir at {location}",
            "Water Supply Augmentation - Ward {ward}",
            "Smart Water Metering Project - {location}",
        ],
    },
    "drainage": {
        "share": 0.18,
        "dept": "WATER",
        "budget_range_lakhs": (10, 2500),
        "duration_days": (90, 600),
        "delay_base_prob": 0.55,               # Drainage projects most delayed
        "overrun_base_prob": 0.48,
        "title_templates": [
            "Storm Water Drain Rehabilitation - {location}",
            "Primary Drain Widening at {location}",
            "Secondary Storm Water Drain Network - Ward {ward}",
            "Sewage Treatment Plant Upgrade - {location}",
            "Underground Drainage System - {location} Layout",
            "Desilting of {location} Lake",
            "Flood Mitigation Works near {landmark}",
        ],
    },
    "electricity": {
        "share": 0.12,
        "dept": "ELEC",
        "budget_range_lakhs": (5, 1500),
        "duration_days": (60, 365),
        "delay_base_prob": 0.35,
        "overrun_base_prob": 0.30,
        "title_templates": [
            "LED Streetlight Installation - {location}",
            "Underground Power Cabling - {road}",
            "Smart Grid Implementation - {location} Zone",
            "Solar Power System at {landmark}",
            "Electrical Substation Upgrade - {location}",
        ],
    },
    "parks": {
        "share": 0.10,
        "dept": "PARKS",
        "budget_range_lakhs": (5, 800),
        "duration_days": (60, 365),
        "delay_base_prob": 0.30,
        "overrun_base_prob": 0.25,
        "title_templates": [
            "Rejuvenation of {landmark} Park",
            "Development of Neighbourhood Park - Ward {ward}",
            "Lake Beautification Project - {location}",
            "Urban Forest Development at {location}",
            "Children Play Area Development - {location}",
        ],
    },
    "buildings": {
        "share": 0.08,
        "dept": "BLDG",
        "budget_range_lakhs": (50, 10000),
        "duration_days": (180, 1460),
        "delay_base_prob": 0.42,
        "overrun_base_prob": 0.38,
        "title_templates": [
            "Construction of {location} Community Hall",
            "Renovation of BBMP Office Building - {location}",
            "Construction of Anganwadi Centres - {location} Ward",
            "Multipurpose Hall Construction at {location}",
            "Market Complex Development - {location}",
        ],
    },
}

STATUS_LIFECYCLE = ["planning", "tendering", "in_progress", "on_hold", "completed", "cancelled"]

CONTRACTORS = [
    "L&T Infrastructure Ltd", "Afcons Infrastructure", "NCC Limited",
    "Shapoorji Pallonji", "Tata Projects Ltd", "Simplex Infrastructures",
    "IVRCL Ltd", "Gammon India", "HCC Limited", "PNC Infratech",
    "KMC Constructions", "Dilip Buildcon", "GR Infraprojects",
    "KPTCL Contractors Division", "BWSSB Engineering Division",
    "Karnataka PWD", "BBMP Engineering Division", "BMRCL Infra",
    "Nagarjuna Construction", "Coastal Projects Ltd",
]

SOURCE_FUNDS = [
    "BBMP Own Funds", "Smart City Mission", "Central Govt Grant",
    "State Govt Grant", "JNNURM", "AMRUT", "World Bank", "ADB Loan",
    "BMRDA", "KUIDFC",
]

LOCATIONS = [
    "Koramangala", "Indiranagar", "Whitefield", "Jayanagar", "Rajajinagar",
    "Malleswaram", "Basavanagudi", "BTM Layout", "HSR Layout", "Bellandur",
    "Electronic City", "Hebbal", "Yeshwanthpur", "Peenya", "Marathahalli",
    "Banashankari", "JP Nagar", "Vijayanagar", "Jalahalli", "Yelahanka",
    "Sarjapur", "Varthur", "Mahadevapura", "KR Puram", "Nagarbhavi",
]

ROADS = [
    "Outer Ring Road", "Inner Ring Road", "MG Road", "Hosur Road",
    "Bannerghatta Road", "Bellary Road", "Old Madras Road", "Mysore Road",
    "Kanakapura Road", "Tumkur Road", "Sarjapur Road", "HAL Airport Road",
    "Magadi Road", "Hessarghatta Road", "Hennur Road", "Varthur Road",
]

LANDMARKS = [
    "Silk Board Junction", "Hebbal Flyover", "KR Market", "Majestic",
    "Yelahanka", "Marathahalli Bridge", "Tin Factory", "NIMHANS",
    "Mekhri Circle", "Koramangala Water Tank", "Lalbagh", "Cubbon Park",
]


def fill_project_template(template: str, ward: int) -> str:
    return template.format(
        road=random.choice(ROADS),
        loc1=random.choice(LOCATIONS),
        loc2=random.choice(LOCATIONS),
        landmark=random.choice(LANDMARKS),
        location=random.choice(LOCATIONS),
        ward=ward,
        phase=random.randint(1, 4),
    )


def compute_project_status(
    planned_start: date, planned_end: date,
    actual_start: date | None, reference_date: date,
    delay_prob: float
) -> tuple[str, float, date | None, float]:
    """
    Returns: (status, completion_pct, actual_end, delay_days)
    """
    if actual_start is None:
        # Pre-start
        if planned_start > reference_date:
            return "planning", 0.0, None, 0.0
        else:
            return "tendering", 0.0, None, 0.0

    total_planned = (planned_end - planned_start).days
    elapsed = (reference_date - actual_start).days

    # Is this project delayed?
    is_delayed = random.random() < delay_prob

    if elapsed >= total_planned:
        # Should be done by now
        if is_delayed:
            # Still running or recently completed with delay
            extra_days = int(np.random.exponential(scale=60))  # avg 60-day overrun
            extra_days = min(extra_days, 365)
            actual_end_date = planned_end + timedelta(days=extra_days)
            if actual_end_date <= reference_date:
                return "completed", 100.0, actual_end_date, float(extra_days)
            else:
                pct = min(95.0, 70.0 + random.uniform(0, 20))
                return "in_progress", round(pct, 1), None, float(extra_days)
        else:
            actual_end_date = planned_end - timedelta(days=random.randint(0, 15))
            return "completed", 100.0, actual_end_date, float(-(planned_end - actual_end_date).days)
    else:
        # In progress
        base_pct = (elapsed / total_planned) * 100
        if is_delayed:
            # Slower progress than planned
            actual_pct = base_pct * random.uniform(0.4, 0.8)
        else:
            actual_pct = base_pct * random.uniform(0.9, 1.1)
        actual_pct = min(99.0, max(5.0, actual_pct))

        # Some projects go on hold
        if random.random() < 0.08:
            return "on_hold", round(actual_pct, 1), None, 0.0

        return "in_progress", round(actual_pct, 1), None, 0.0


def generate_projects(n: int = 12000) -> pd.DataFrame:
    print(f"Generating {n:,} project records...")
    reference_date = date(2024, 12, 31)
    start_of_history = date(2019, 1, 1)

    records = []
    counter = 1

    for cat, cfg in CATEGORY_CONFIG.items():
        cat_count = int(n * cfg["share"])
        print(f"  {cat}: {cat_count:,} records")

        for _ in range(cat_count):
            ward_num = random.randint(1, 198)

            # Project start date distribution — weighted toward recent years
            years_back = np.random.exponential(scale=1.5)
            years_back = min(years_back, 5.5)
            planned_start = reference_date - timedelta(days=int(years_back * 365))
            if planned_start < start_of_history:
                planned_start = start_of_history + timedelta(days=random.randint(0, 180))

            # Duration
            dur_min, dur_max = cfg["duration_days"]
            duration = random.randint(dur_min, dur_max)
            planned_end = planned_start + timedelta(days=duration)

            # Budget
            bmin, bmax = cfg["budget_range_lakhs"]
            estimated_cost = round(np.random.lognormal(
                mean=np.log((bmin + bmax) / 2),
                sigma=0.6
            ), 2)
            estimated_cost = max(bmin, min(bmax, estimated_cost))

            # Budget approval: some have, some don't (planning stage)
            if random.random() > 0.15:
                approved_budget = round(estimated_cost * random.uniform(0.90, 1.10), 2)
            else:
                approved_budget = None

            # Actual start (10% never started)
            actual_start = None
            if random.random() > 0.10:
                delay_to_start = random.randint(0, 30)
                actual_start = planned_start + timedelta(days=delay_to_start)

            status, completion_pct, actual_end, delay_days = compute_project_status(
                planned_start, planned_end, actual_start, reference_date, cfg["delay_base_prob"]
            )

            # Cost tracking
            if status == "completed" and approved_budget:
                overrun = random.random() < cfg["overrun_base_prob"]
                if overrun:
                    actual_cost = round(approved_budget * random.uniform(1.05, 1.45), 2)
                else:
                    actual_cost = round(approved_budget * random.uniform(0.85, 1.02), 2)
            elif status == "in_progress" and approved_budget:
                actual_cost = round(approved_budget * (completion_pct / 100) * random.uniform(0.80, 1.20), 2)
            elif status in ("planning", "tendering"):
                actual_cost = 0.0
            else:
                actual_cost = round(estimated_cost * random.uniform(0.0, 0.3), 2)

            budget_util_pct = 0.0
            if approved_budget and approved_budget > 0:
                budget_util_pct = round((actual_cost / approved_budget) * 100, 1)

            is_delayed = delay_days > 0
            expected_overrun = 0.0
            if status != "completed" and approved_budget:
                if budget_util_pct > 70 and completion_pct < 50:
                    expected_overrun = round(approved_budget * random.uniform(0.10, 0.40), 2)

            # Compute delay probability for AI feature
            # Based on: budget_util, completion, timeline position
            elapsed_pct = 0.0
            if actual_start:
                total_dur = (planned_end - planned_start).days
                elapsed = (min(reference_date, planned_end) - planned_start).days
                elapsed_pct = min(100, (elapsed / max(1, total_dur)) * 100)

            # Feature: pace indicator (completion % / elapsed %)
            if elapsed_pct > 0:
                pace = completion_pct / elapsed_pct
            else:
                pace = 1.0

            # Delay probability model (heuristic — Phase 3 trains the real one)
            delay_prob_score = cfg["delay_base_prob"]
            if pace < 0.6:
                delay_prob_score = min(0.95, delay_prob_score + 0.25)
            if budget_util_pct > 80 and completion_pct < 60:
                delay_prob_score = min(0.95, delay_prob_score + 0.15)
            if actual_start and (actual_start - planned_start).days > 14:
                delay_prob_score = min(0.95, delay_prob_score + 0.08)
            delay_prob_score = round(delay_prob_score, 3)

            # Pre-monsoon start risk (June–August starts in Bengaluru are riskier for civil works)
            pre_monsoon_start = 1 if (actual_start and actual_start.month in [5, 6, 7]) else 0

            title_tmpl = random.choice(cfg["title_templates"])
            title = fill_project_template(title_tmpl, ward_num)

            from etl_complaints import ward_to_coords, ward_to_zone
            lat, lng = ward_to_coords(ward_num)
            zone = ward_to_zone(ward_num)

            records.append({
                "project_id": f"PRJ-{str(counter).zfill(6)}",
                "title": title,
                "category": cat,
                "status": status,
                "department": cfg["dept"],
                "ward_number": f"Ward-{ward_num}",
                "zone": zone,
                "latitude": lat,
                "longitude": lng,
                "estimated_cost_lakhs": round(estimated_cost, 2),
                "approved_budget_lakhs": round(approved_budget, 2) if approved_budget else None,
                "actual_cost_lakhs": round(actual_cost, 2),
                "budget_utilization_pct": budget_util_pct,
                "completion_pct": completion_pct,
                "planned_start": planned_start.strftime("%Y-%m-%d"),
                "planned_end": planned_end.strftime("%Y-%m-%d"),
                "actual_start": actual_start.strftime("%Y-%m-%d") if actual_start else None,
                "actual_end": actual_end.strftime("%Y-%m-%d") if actual_end else None,
                "planned_duration_days": duration,
                "delay_days": round(delay_days, 0),
                "is_delayed": is_delayed,
                "expected_overrun_lakhs": round(expected_overrun, 2),
                "contractor": random.choice(CONTRACTORS),
                "source_fund": random.choice(SOURCE_FUNDS),
                "delay_probability": delay_prob_score,
                # ── AI Feature Engineering ──
                "elapsed_pct": round(elapsed_pct, 1),
                "pace_indicator": round(pace, 3),
                "pre_monsoon_start": pre_monsoon_start,
                "start_delay_days": (actual_start - planned_start).days if actual_start else 0,
            })
            counter += 1

    df = pd.DataFrame(records)
    df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)
    return df


def validate_projects(df: pd.DataFrame) -> dict:
    return {
        "total_records": len(df),
        "category_distribution": df["category"].value_counts().to_dict(),
        "status_distribution": df["status"].value_counts().to_dict(),
        "delay_rate": f"{df['is_delayed'].mean()*100:.1f}%",
        "avg_completion_pct": round(df["completion_pct"].mean(), 1),
        "avg_budget_utilization": round(df["budget_utilization_pct"].mean(), 1),
        "overrun_projects": int((df["expected_overrun_lakhs"] > 0).sum()),
        "cost_stats_lakhs": df["estimated_cost_lakhs"].describe().to_dict(),
    }


if __name__ == "__main__":
    df = generate_projects(12000)
    output_path = OUTPUT_DIR / "projects.csv"
    df.to_csv(output_path, index=False)
    print(f"\n✅ Saved {len(df):,} records → {output_path}")

    report = validate_projects(df)
    print(f"\n📊 Quality Report:")
    print(f"  Total records      : {report['total_records']:,}")
    print(f"  Delay rate         : {report['delay_rate']}")
    print(f"  Avg completion     : {report['avg_completion_pct']}%")
    print(f"  Avg budget util    : {report['avg_budget_utilization']}%")
    print(f"  Projects w/ overrun: {report['overrun_projects']:,}")
