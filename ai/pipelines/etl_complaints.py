"""
CivilInc ETL Pipeline — Complaints Dataset
============================================
Generates 55,000+ training-ready complaint records modeled on:
  - NYC 311 Service Request category distributions (nyc.gov/open-data)
  - Chicago 311 Service Request patterns (data.cityofchicago.org)
  - BBMP helpline complaint taxonomy
  - Bengaluru ward geography (198 BBMP wards)

Transformations applied:
  - Category normalization to 7 standard classes
  - Geographic remapping to Bengaluru ward centroids
  - Resolution time modeling per category SLA benchmarks
  - Priority assignment based on category × resolution_time
  - SLA breach calculation per department SLA config
  - Synthetic description generation with category-specific vocabulary
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import string
import json
from pathlib import Path

SEED = 42
np.random.seed(SEED)
random.seed(SEED)

OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ─── Bengaluru Ward Geography ────────────────────────────────────────────────
# 198 BBMP wards mapped to 5 zones with approximate centroids
ZONE_BOUNDS = {
    "South":   {"lat": (12.87, 12.96), "lng": (77.55, 77.65), "wards": list(range(1, 41))},
    "East":    {"lat": (12.95, 13.05), "lng": (77.65, 77.78), "wards": list(range(41, 81))},
    "North":   {"lat": (13.02, 13.15), "lng": (77.55, 77.68), "wards": list(range(81, 121))},
    "West":    {"lat": (12.95, 13.05), "lng": (77.42, 77.56), "wards": list(range(121, 161))},
    "Central": {"lat": (12.96, 13.02), "lng": (77.56, 77.65), "wards": list(range(161, 199))},
}

def ward_to_coords(ward_num: int) -> tuple[float, float]:
    for zone, cfg in ZONE_BOUNDS.items():
        if ward_num in cfg["wards"]:
            lat = np.random.uniform(*cfg["lat"])
            lng = np.random.uniform(*cfg["lng"])
            # Add ~50m jitter so complaints in same ward don't stack exactly
            lat += np.random.normal(0, 0.001)
            lng += np.random.normal(0, 0.001)
            return round(lat, 6), round(lng, 6)
    return round(np.random.uniform(12.87, 13.10), 6), round(np.random.uniform(77.45, 77.78), 6)

def ward_to_zone(ward_num: int) -> str:
    for zone, cfg in ZONE_BOUNDS.items():
        if ward_num in cfg["wards"]:
            return zone
    return "Central"

# ─── Category Configuration ──────────────────────────────────────────────────
# Distributions modeled on NYC 311 (2019–2023) adapted for Bengaluru context
CATEGORY_CONFIG = {
    "roads": {
        "share": 0.28,           # 28% of complaints — roads dominate in Indian cities
        "dept": "ROADS",
        "sla_hours": 48,
        "sub_categories": ["Pothole", "Road Damage", "Footpath Obstruction",
                           "Encroachment", "Speed Breaker", "Traffic Signal Fault",
                           "Road Marking", "Bridge Damage"],
        "resolution_days_dist": {"mean": 8.5, "std": 5.2, "min": 1, "max": 45},
        "priority_weights": {"low": 0.15, "medium": 0.40, "high": 0.35, "critical": 0.10},
        "title_templates": [
            "Pothole on {road} causing accidents",
            "Road damage near {landmark}",
            "Encroachment on footpath at {location}",
            "Traffic signal not working at {junction}",
            "Broken road divider on {road}",
            "Large crater on main road near {landmark}",
            "Speed breaker damaged on {road}",
        ],
    },
    "water_supply": {
        "share": 0.20,
        "dept": "WATER",
        "sla_hours": 24,
        "sub_categories": ["No Water Supply", "Low Pressure", "Contaminated Water",
                           "Pipe Leakage", "Meter Fault", "Billing Issue", "New Connection"],
        "resolution_days_dist": {"mean": 4.2, "std": 3.1, "min": 1, "max": 30},
        "priority_weights": {"low": 0.10, "medium": 0.35, "high": 0.40, "critical": 0.15},
        "title_templates": [
            "No water supply in {location} for {days} days",
            "Water pipe burst on {road}",
            "Contaminated water supply in {location}",
            "Low water pressure in {location}",
            "Water meter not working at {address}",
            "Water leakage from main pipeline near {landmark}",
        ],
    },
    "drainage": {
        "share": 0.18,
        "dept": "WATER",
        "sla_hours": 36,
        "sub_categories": ["Blocked Drain", "Overflowing Drain", "Storm Water Flooding",
                           "Sewage Overflow", "Manhole Open", "Drain Maintenance"],
        "resolution_days_dist": {"mean": 6.8, "std": 4.5, "min": 1, "max": 40},
        "priority_weights": {"low": 0.10, "medium": 0.35, "high": 0.38, "critical": 0.17},
        "title_templates": [
            "Storm drain blocked causing flooding near {landmark}",
            "Open manhole on {road} posing safety risk",
            "Sewage overflow on {road}",
            "Drain overflowing into residential area at {location}",
            "Waterlogging on {road} during rains",
        ],
    },
    "electricity": {
        "share": 0.15,
        "dept": "ELEC",
        "sla_hours": 12,
        "sub_categories": ["Streetlight Not Working", "Power Outage", "Transformer Fault",
                           "Fallen Pole", "Exposed Wires", "Billing Issue", "New Connection"],
        "resolution_days_dist": {"mean": 2.8, "std": 2.1, "min": 1, "max": 20},
        "priority_weights": {"low": 0.20, "medium": 0.45, "high": 0.28, "critical": 0.07},
        "title_templates": [
            "Streetlight not working near {landmark}",
            "Power outage in {location} for {days} hours",
            "Fallen electric pole on {road}",
            "Exposed live wires near {landmark}",
            "Transformer fault causing blackout in {location}",
        ],
    },
    "parks": {
        "share": 0.07,
        "dept": "PARKS",
        "sla_hours": 72,
        "sub_categories": ["Broken Equipment", "Garbage Dumping", "Encroachment",
                           "Poor Maintenance", "Lighting Issue", "Tree Fallen"],
        "resolution_days_dist": {"mean": 12.5, "std": 7.0, "min": 2, "max": 60},
        "priority_weights": {"low": 0.40, "medium": 0.40, "high": 0.18, "critical": 0.02},
        "title_templates": [
            "Park benches broken and not maintained at {location}",
            "Garbage dumping in public park near {landmark}",
            "Tree fallen blocking park entrance at {location}",
            "Playground equipment broken at {location} park",
            "Park encroachment by vendors near {landmark}",
        ],
    },
    "buildings": {
        "share": 0.07,
        "dept": "BLDG",
        "sla_hours": 96,
        "sub_categories": ["Unauthorized Construction", "Dangerous Building",
                           "Permit Violation", "Demolition Required", "Height Violation"],
        "resolution_days_dist": {"mean": 18.0, "std": 9.0, "min": 3, "max": 90},
        "priority_weights": {"low": 0.25, "medium": 0.40, "high": 0.28, "critical": 0.07},
        "title_templates": [
            "Unauthorized construction near {location}",
            "Dilapidated building posing danger on {road}",
            "Building permit violation at {address}",
            "Dangerous structure collapse risk near {landmark}",
        ],
    },
    "sanitation": {
        "share": 0.05,
        "dept": "SWM",
        "sla_hours": 24,
        "sub_categories": ["Garbage Not Collected", "Waste Burning", "Garbage Dump",
                           "Vehicle Not Coming", "Bulk Waste"],
        "resolution_days_dist": {"mean": 3.5, "std": 2.8, "min": 1, "max": 25},
        "priority_weights": {"low": 0.20, "medium": 0.45, "high": 0.28, "critical": 0.07},
        "title_templates": [
            "Garbage not collected in {location} for {days} days",
            "Illegal waste dumping near {landmark}",
            "Garbage burning causing air pollution at {location}",
            "Overflowing garbage bins on {road}",
        ],
    },
}

# ─── Bengaluru Location Vocabulary ───────────────────────────────────────────
ROADS = [
    "MG Road", "Residency Road", "Koramangala 5th Block", "Indiranagar 100ft Road",
    "Whitefield Main Road", "Hosur Road", "Bannerghatta Road", "Bellary Road",
    "Old Madras Road", "Mysore Road", "Kanakapura Road", "Tumkur Road",
    "Outer Ring Road", "Inner Ring Road", "Sarjapur Road", "Electronic City Flyover",
    "HAL Airport Road", "Richmond Road", "St Marks Road", "Vittal Mallya Road",
    "JP Nagar Main Road", "BTM Layout Main Road", "HSR Layout Sector 7",
    "Rajajinagar Main Road", "Yeshwanthpur Main Road", "Peenya Industrial Road",
]

LANDMARKS = [
    "Silk Board Junction", "KR Market", "Majestic Bus Stand", "Jayanagar 4th Block",
    "Koramangala Water Tank", "Indiranagar Metro Station", "Whitefield IT Park",
    "Hebbal Flyover", "Banashankari Temple", "Lalbagh Botanical Garden",
    "Cubbon Park", "UB City Mall", "Forum Mall Koramangala", "Phoenix Mall Whitefield",
    "Electronic City Phase 1", "Bellandur Lake", "Varthur Lake", "Ulsoor Lake",
    "NIMHANS Circle", "Mekhri Circle", "Tin Factory", "KR Puram Signal",
    "Marathahalli Bridge", "Agara Lake", "RV College Circle",
]

LOCATIONS = [
    "Koramangala", "Indiranagar", "Whitefield", "Jayanagar", "Rajajinagar",
    "Malleswaram", "Basavanagudi", "BTM Layout", "HSR Layout", "Bellandur",
    "Sarjapur", "Electronic City", "Hebbal", "Yeshwanthpur", "Peenya",
    "Marathahalli", "Varthur", "KR Puram", "Mahadevapura", "Yelahanka",
    "Banashankari", "JP Nagar", "Padmanabhanagar", "Kengeri", "Rajarajeshwari Nagar",
    "Vijayanagar", "Jalahalli", "Bagalgunte", "Dasarahalli", "Nagarbhavi",
]

SOURCE_DIST = {"web": 0.45, "mobile": 0.38, "ivr": 0.10, "whatsapp": 0.07}

STATUS_TERMINAL = {"resolved", "closed", "rejected"}

def generate_description(category: str, title: str, sub_category: str) -> str:
    """Generate realistic complaint descriptions from templates."""
    templates = {
        "roads": [
            f"The {sub_category.lower()} issue has been present for several days and is causing significant inconvenience to residents and commuters. Vehicles are getting damaged and pedestrian movement is affected. Immediate intervention is required from the Roads department to address this critical safety concern.",
            f"Residents of this area have been suffering due to this {sub_category.lower()} problem. Multiple complaints have been raised verbally but no action has been taken. This is causing accidents and damage to vehicles. Requesting urgent attention from BBMP Roads division.",
            f"This {sub_category.lower()} has existed for over two weeks now. Despite heavy rains the situation has worsened. Several two-wheelers have fallen and there have been near-miss accidents. Please depute a team for immediate repair.",
        ],
        "water_supply": [
            f"The water supply to our area has been severely disrupted. {sub_category} is affecting over 200 households in this ward. Residents are spending large amounts on water tankers. BWSSB should investigate the pipeline and restore supply at the earliest.",
            f"We have been facing {sub_category.lower()} issue for several days. The situation is critical especially during summer. Children and elderly residents are facing severe hardship. Requesting BWSSB to take immediate corrective action.",
            f"The {sub_category.lower()} has caused major disruption to daily life. Local businesses and residences are both affected. We have already raised this issue with the local ward councillor but there has been no response. Urgent action needed.",
        ],
        "drainage": [
            f"The drainage system near our area is completely blocked and causing waterlogging. During rain, the entire road gets flooded making it impassable. This {sub_category.lower()} has been present for months. Requesting BBMP drainage division to clear and repair the storm water drain.",
            f"Sewage and rainwater are mixing due to {sub_category.lower()} creating a severe public health hazard. The stench is unbearable and mosquito breeding has increased significantly. This is a health emergency and needs immediate attention.",
            f"The {sub_category.lower()} is causing flooding in residential basements and ground floor apartments. Repeated rains have made the situation critical. BBMP drainage department must take immediate action to prevent further damage.",
        ],
        "electricity": [
            f"The {sub_category.lower()} has been reported multiple times to BESCOM but no action has been taken. This is causing safety hazards especially at night. Residents are unable to walk safely. Requesting immediate repair.",
            f"Due to {sub_category.lower()} our area has been facing issues for several days. Businesses are suffering heavy losses. Backup generators are not feasible for all. BESCOM should prioritize this repair immediately.",
            f"The {sub_category.lower()} poses a serious safety risk to pedestrians and motorists. Children returning from school pass through this area and are at risk. Please take urgent action to rectify this electrical fault.",
        ],
        "parks": [
            f"The public park in our area is in a terrible state. {sub_category} is making it unusable for residents especially senior citizens and children. BBMP Parks department has been negligent in maintenance. Requesting immediate attention.",
            f"Despite being a designated public space, the park is facing {sub_category.lower()} issues. Residents use this space for morning and evening walks but conditions are deteriorating. Proper maintenance must be carried out regularly.",
        ],
        "buildings": [
            f"There is {sub_category.lower()} happening in our neighborhood which is clearly illegal. Despite multiple complaints to the local ward office no action has been taken. BBMP building inspection team should visit and take appropriate legal action.",
            f"The {sub_category.lower()} is a serious concern for neighboring residents. The structure appears dangerous and may collapse. Requesting BBMP to conduct an inspection and issue necessary notices to the owner.",
        ],
        "sanitation": [
            f"Garbage collection vehicle has not come to our area for several days. {sub_category} is leading to heaps of waste on the roadside attracting stray animals and creating health hazards. BBMP Solid Waste Management must restore regular service.",
            f"The {sub_category.lower()} issue in our locality is causing severe health and hygiene problems. Residents have raised this issue multiple times without resolution. Requesting immediate action from BBMP SWM department.",
        ],
    }
    options = templates.get(category, templates["roads"])
    return random.choice(options)

def fill_template(template: str, category: str) -> str:
    """Fill location/road/landmark placeholders."""
    return template.format(
        road=random.choice(ROADS),
        landmark=random.choice(LANDMARKS),
        location=random.choice(LOCATIONS),
        address=f"{random.randint(1, 500)}, {random.choice(ROADS)}",
        junction=random.choice(LANDMARKS) + " Junction",
        days=random.randint(2, 14),
    )

def assign_status(resolution_days: float, created_date: datetime,
                  reference_date: datetime) -> str:
    """Assign realistic status based on resolution time and age."""
    age_days = (reference_date - created_date).days
    if resolution_days is not None and resolution_days > 0:
        if age_days >= resolution_days:
            return random.choices(
                ["resolved", "closed"],
                weights=[0.75, 0.25]
            )[0]
    # Unresolved complaints
    if age_days < 3:
        return random.choices(
            ["pending", "under_review"],
            weights=[0.70, 0.30]
        )[0]
    elif age_days < 10:
        return random.choices(
            ["under_review", "assigned", "in_progress"],
            weights=[0.20, 0.45, 0.35]
        )[0]
    elif age_days < 30:
        return random.choices(
            ["assigned", "in_progress", "escalated"],
            weights=[0.30, 0.55, 0.15]
        )[0]
    else:
        return random.choices(
            ["in_progress", "escalated", "rejected"],
            weights=[0.50, 0.35, 0.15]
        )[0]

def compute_priority(category: str, resolution_days: float,
                     sub_category: str, sla_hours: int) -> str:
    """Derive priority from category weights + resolution time signal."""
    weights = CATEGORY_CONFIG[category]["priority_weights"]
    base = random.choices(
        list(weights.keys()),
        weights=list(weights.values())
    )[0]

    # Override with resolution time heuristic
    sla_days = sla_hours / 24
    if resolution_days is not None:
        if resolution_days > sla_days * 3:
            return random.choices(["high", "critical"], weights=[0.6, 0.4])[0]
        elif resolution_days < sla_days * 0.5:
            return random.choices(["low", "medium"], weights=[0.5, 0.5])[0]

    # Critical sub-categories
    critical_keywords = ["fallen", "burst", "collapse", "flood", "exposed", "overflow", "dangerous", "emergency"]
    if any(kw in sub_category.lower() for kw in critical_keywords):
        if base in ("low", "medium"):
            return "high"

    return base


def generate_complaints(n: int = 55000) -> pd.DataFrame:
    print(f"Generating {n:,} complaint records...")

    reference_date = datetime(2024, 12, 31)
    start_date = datetime(2022, 1, 1)
    total_days = (reference_date - start_date).days

    records = []
    counter = 1

    for cat, cfg in CATEGORY_CONFIG.items():
        cat_count = int(n * cfg["share"])
        print(f"  {cat}: {cat_count:,} records")

        for _ in range(cat_count):
            # Temporal distribution: more recent complaints dominate (realistic)
            age_days = int(np.random.exponential(scale=180))
            age_days = min(age_days, total_days)
            created_date = reference_date - timedelta(days=age_days)
            created_date += timedelta(
                hours=random.randint(6, 22),
                minutes=random.randint(0, 59),
            )

            sub_cat = random.choice(cfg["sub_categories"])
            ward_num = random.randint(1, 198)
            lat, lng = ward_to_coords(ward_num)
            zone = ward_to_zone(ward_num)

            # Resolution time
            d = cfg["resolution_days_dist"]
            res_days_raw = np.random.normal(d["mean"], d["std"])
            res_days = max(d["min"], min(d["max"], res_days_raw))

            # Some complaints are unresolved (20%)
            is_resolved = random.random() > 0.20
            resolution_days = round(res_days, 1) if is_resolved else None

            resolved_date = None
            if is_resolved and resolution_days is not None:
                resolved_date = created_date + timedelta(days=resolution_days)
                if resolved_date > reference_date:
                    resolved_date = None
                    is_resolved = False
                    resolution_days = None

            status = assign_status(resolution_days, created_date, reference_date)
            priority = compute_priority(cat, resolution_days, sub_cat, cfg["sla_hours"])

            # SLA breach
            sla_days = cfg["sla_hours"] / 24
            sla_breached = False
            if resolution_days is not None and resolution_days > sla_days:
                sla_breached = True
            elif status in {"escalated", "in_progress"} and age_days > sla_days:
                sla_breached = True

            escalation = 0
            if sla_breached:
                escalation = random.choices([1, 2, 3], weights=[0.60, 0.30, 0.10])[0]

            title_tmpl = random.choice(cfg["title_templates"])
            title = fill_template(title_tmpl, cat)
            description = generate_description(cat, title, sub_cat)

            # Citizen rating (only if resolved)
            citizen_rating = None
            if status in {"resolved", "closed"}:
                if random.random() > 0.35:  # 65% feedback rate
                    if resolution_days and resolution_days <= sla_days:
                        citizen_rating = random.choices([3, 4, 5], weights=[0.15, 0.40, 0.45])[0]
                    else:
                        citizen_rating = random.choices([1, 2, 3, 4], weights=[0.25, 0.35, 0.25, 0.15])[0]

            source = random.choices(
                list(SOURCE_DIST.keys()),
                weights=list(SOURCE_DIST.values())
            )[0]

            records.append({
                "complaint_id": f"CMP-{str(counter).zfill(7)}",
                "title": title,
                "description": description,
                "category": cat,
                "sub_category": sub_cat,
                "status": status,
                "priority": priority,
                "ward_number": f"Ward-{ward_num}",
                "zone": zone,
                "latitude": lat,
                "longitude": lng,
                "department": cfg["dept"],
                "created_date": created_date.strftime("%Y-%m-%d %H:%M:%S"),
                "resolved_date": resolved_date.strftime("%Y-%m-%d %H:%M:%S") if resolved_date else None,
                "resolution_days": resolution_days,
                "sla_hours": cfg["sla_hours"],
                "sla_breached": sla_breached,
                "escalation_level": escalation,
                "citizen_rating": citizen_rating,
                "source": source,
                "ai_cluster_id": None,  # Phase 3 fills this
            })
            counter += 1

    df = pd.DataFrame(records)
    df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)
    return df


def validate_complaints(df: pd.DataFrame) -> dict:
    """Data quality checks."""
    report = {
        "total_records": len(df),
        "missing_values": df.isnull().sum().to_dict(),
        "category_distribution": df["category"].value_counts().to_dict(),
        "status_distribution": df["status"].value_counts().to_dict(),
        "priority_distribution": df["priority"].value_counts().to_dict(),
        "source_distribution": df["source"].value_counts().to_dict(),
        "zone_distribution": df["zone"].value_counts().to_dict(),
        "resolution_stats": df["resolution_days"].describe().to_dict(),
        "sla_breach_rate": f"{df['sla_breached'].mean()*100:.1f}%",
        "feedback_rate": f"{df['citizen_rating'].notna().mean()*100:.1f}%",
        "avg_rating": round(df["citizen_rating"].mean(), 2),
        "date_range": {
            "min": df["created_date"].min(),
            "max": df["created_date"].max(),
        },
    }
    return report


if __name__ == "__main__":
    df = generate_complaints(55000)
    output_path = OUTPUT_DIR / "complaints.csv"
    df.to_csv(output_path, index=False)
    print(f"\n✅ Saved {len(df):,} records → {output_path}")

    report = validate_complaints(df)
    print(f"\n📊 Quality Report:")
    print(f"  Total records    : {report['total_records']:,}")
    print(f"  Category spread  : {list(report['category_distribution'].keys())}")
    print(f"  SLA breach rate  : {report['sla_breach_rate']}")
    print(f"  Feedback rate    : {report['feedback_rate']}")
    print(f"  Avg citizen rating: {report['avg_rating']}")
    print(f"  Resolution days  : mean={report['resolution_stats']['mean']:.1f}, "
          f"std={report['resolution_stats']['std']:.1f}")

    with open(OUTPUT_DIR.parent / "quality_reports" / "complaints_quality.json", "w") as f:
        # Convert to JSON-serializable
        safe = {k: (str(v) if not isinstance(v, (int, float, str, dict, list, bool, type(None))) else v)
                for k, v in report.items()}
        json.dump(safe, f, indent=2, default=str)
    print(f"  Quality report   → data/quality_reports/complaints_quality.json")
