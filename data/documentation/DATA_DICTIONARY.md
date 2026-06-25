# CivilInc Data Dictionary

## Source Lineage

| Dataset | Primary Sources | Transformation |
|---|---|---|
| complaints.csv | NYC 311 (nyc.gov/open-data), Chicago 311 (data.cityofchicago.org), India OGD, BBMP Open Data | Category normalization, ward mapping, coordinate synthesis for Bengaluru geography |
| projects.csv | Bengaluru Smart City Reports 2019–2024, BBMP project tracker, OpenStreetMap POI data | Budget normalization (INR), status standardization, GIS coordinate assignment |
| budgets.csv | India OGD department budgets, BBMP Annual Reports 2019–2024 | Multi-year restructuring, INR normalization, utilization calculation |
| citizen_feedback.csv | Synthesized from NYC 311 satisfaction surveys, BBMP helpline records | Rating normalization 1–5, sentiment labeling |
| officer_workload.csv | Derived from complaints + projects datasets | Aggregation by officer/department/period |

## Field Definitions

### complaints.csv
| Field | Type | Description | Source |
|---|---|---|---|
| complaint_id | string | Unique identifier CMP-XXXXXXX | Generated |
| title | string | Short description of issue | NYC/Chicago 311, normalized |
| description | string | Full complaint text | NYC/Chicago 311, adapted |
| category | string | Normalized: roads/water_supply/drainage/electricity/parks/buildings/sanitation | Mapped from source categories |
| sub_category | string | Detailed sub-type | Source-specific |
| status | string | pending/under_review/assigned/in_progress/resolved/closed/rejected | Mapped |
| priority | string | low/medium/high/critical | Derived from category + resolution_time |
| ward_number | string | Ward-1 to Ward-198 (BBMP ward range) | Mapped from NYC/Chicago districts |
| zone | string | North/South/East/West/Central Bengaluru | Derived from ward |
| latitude | float | Bengaluru-range coordinates (12.7–13.2°N) | Synthesized from ward centroids |
| longitude | float | Bengaluru-range coordinates (77.4–77.8°E) | Synthesized from ward centroids |
| created_date | datetime | Complaint creation timestamp | Source date, year-shifted to 2022–2024 |
| resolved_date | datetime | Resolution timestamp (null if unresolved) | Source date |
| resolution_days | int | Days from creation to resolution | Calculated |
| department | string | Responsible department code | Mapped from category |
| citizen_rating | int | 1–5 satisfaction score | From feedback dataset |
| source | string | web/mobile/ivr/whatsapp | Distribution modeled on BBMP data |
| sla_breached | bool | Whether SLA was exceeded | Calculated from resolution_days vs SLA |
| escalation_level | int | 0–3 escalation count | Derived from resolution_days |
| ai_cluster_id | int | Cluster assignment (Phase 3) | Placeholder null |

### projects.csv
| Field | Type | Description |
|---|---|---|
| project_id | string | PRJ-XXXXXX |
| title | string | Project name |
| category | string | roads/water_supply/drainage/electricity/parks/buildings |
| status | string | planning/tendering/in_progress/on_hold/completed/cancelled |
| department | string | Department code |
| ward_number | string | Primary ward |
| zone | string | City zone |
| estimated_cost | float | Budget estimate in INR lakhs |
| approved_budget | float | Sanctioned budget INR lakhs |
| actual_cost | float | Spent to date INR lakhs |
| budget_utilization_pct | float | actual/approved × 100 |
| completion_pct | float | 0–100 |
| planned_start | date | Planned start date |
| planned_end | date | Planned end date |
| actual_start | date | Actual start |
| actual_end | date | Actual end (null if ongoing) |
| delay_days | int | Actual end – Planned end (negative = early) |
| is_delayed | bool | delay_days > 0 |
| contractor | string | Contractor name |
| source_fund | string | BBMP/Smart City/Central Govt/State Govt |
| latitude | float | Project location |
| longitude | float | Project location |

### budgets.csv
| Field | Type | Description |
|---|---|---|
| year | int | Financial year (2019–2024) |
| department | string | Department code |
| allocated | float | Annual allocation INR lakhs |
| utilized | float | Amount spent INR lakhs |
| utilization_pct | float | utilized/allocated × 100 |
| previous_year_utilized | float | Prior year spend |
| yoy_growth_pct | float | Year-over-year allocation growth |
| project_count | int | Active projects that year |
| complaint_count | int | Complaints handled that year |

### citizen_feedback.csv
| Field | Type | Description |
|---|---|---|
| feedback_id | string | FBK-XXXXXXX |
| complaint_id | string | Linked complaint |
| rating | int | 1–5 stars |
| sentiment | string | positive/neutral/negative |
| feedback_text | string | Free text comment |
| response_time_days | int | Days to first response |
| resolution_satisfactory | bool | Rating >= 3 |
| submitted_date | datetime | Feedback submission |

### officer_workload.csv
| Field | Type | Description |
|---|---|---|
| officer_id | string | Officer reference |
| department | string | Department code |
| period | string | YYYY-MM |
| complaints_assigned | int | Complaints in period |
| complaints_resolved | int | Resolved in period |
| avg_resolution_days | float | Average days to resolve |
| projects_managed | int | Active projects |
| sla_breach_count | int | SLA violations |
| workload_score | float | Normalized 0–1 composite score |
