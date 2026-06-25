"""
CivilInc Seed Script
Loads production-realistic seed data for development and staging.
Run: python scripts/seed.py
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings
from app.core.security import security
from app.core.permissions import Role
from app.models.user import User
from app.models.department import Department
from app.models.complaint import Complaint
from app.models.project import Project
from app.models.forum import ForumThread
from app.models.notification import Notification


DEPARTMENTS = [
    {"name": "Roads & Infrastructure", "code": "ROADS", "sla_hours": 48, "annual_budget": 50000000,
     "complaint_categories": ["roads", "transportation"], "email": "roads@civilinc.gov.in",
     "description": "Responsible for road construction, maintenance, and traffic management."},
    {"name": "Water Supply & Sewerage", "code": "WATER", "sla_hours": 24, "annual_budget": 35000000,
     "complaint_categories": ["water_supply", "drainage"], "email": "water@civilinc.gov.in",
     "description": "Manages potable water distribution and sewerage network."},
    {"name": "Electricity & Streetlights", "code": "ELEC", "sla_hours": 12, "annual_budget": 20000000,
     "complaint_categories": ["electricity"], "email": "electricity@civilinc.gov.in",
     "description": "Maintains electrical infrastructure and public lighting."},
    {"name": "Parks & Horticulture", "code": "PARKS", "sla_hours": 72, "annual_budget": 10000000,
     "complaint_categories": ["parks"], "email": "parks@civilinc.gov.in",
     "description": "Develops and maintains urban green spaces and gardens."},
    {"name": "Buildings & Planning", "code": "BLDG", "sla_hours": 96, "annual_budget": 25000000,
     "complaint_categories": ["buildings"], "email": "buildings@civilinc.gov.in",
     "description": "Building permits, encroachment control, and urban planning."},
    {"name": "Solid Waste Management", "code": "SWM", "sla_hours": 24, "annual_budget": 15000000,
     "complaint_categories": ["sanitation"], "email": "swm@civilinc.gov.in",
     "description": "Garbage collection, segregation, and disposal."},
]

USERS = [
    {"email": "commissioner@civilinc.gov.in", "full_name": "Dr. Rajesh Kumar", "role": Role.COMMISSIONER,
     "employee_id": "COMM001", "designation": "Municipal Commissioner", "phone": "+91-80-22223333",
     "ward_number": None, "password": "Admin@1234"},
    {"email": "engineer.roads@civilinc.gov.in", "full_name": "Priya Sharma", "role": Role.ENGINEER,
     "employee_id": "ENG001", "designation": "Executive Engineer - Roads", "phone": "+91-80-22224444",
     "dept_code": "ROADS", "password": "Engineer@1234"},
    {"email": "engineer.water@civilinc.gov.in", "full_name": "Suresh Nair", "role": Role.ENGINEER,
     "employee_id": "ENG002", "designation": "Executive Engineer - Water", "phone": "+91-80-22225555",
     "dept_code": "WATER", "password": "Engineer@1234"},
    {"email": "coordinator@civilinc.gov.in", "full_name": "Anita Desai", "role": Role.COORDINATOR,
     "employee_id": "CRD001", "designation": "Citizen Services Coordinator", "phone": "+91-80-22226666",
     "dept_code": "ROADS", "password": "Coord@1234"},
    {"email": "citizen1@example.com", "full_name": "Ravi Verma", "role": Role.CITIZEN,
     "ward_number": "Ward-42", "phone": "+91-9876543210", "password": "Citizen@1234"},
    {"email": "citizen2@example.com", "full_name": "Meera Pillai", "role": Role.CITIZEN,
     "ward_number": "Ward-15", "phone": "+91-9876543211", "password": "Citizen@1234"},
    {"email": "citizen3@example.com", "full_name": "Arjun Mehta", "role": Role.CITIZEN,
     "ward_number": "Ward-7", "phone": "+91-9876543212", "password": "Citizen@1234"},
]

SAMPLE_COMPLAINTS = [
    {"title": "Large pothole causing accidents near Silk Board Junction",
     "description": "There is a massive pothole on the main road near Silk Board which has already caused 3 accidents this week. Urgent repair needed immediately.",
     "category": "roads", "priority": "critical", "status": "assigned",
     "ward_number": "Ward-29", "latitude": 12.9176, "longitude": 77.6237,
     "address": "Silk Board Junction, Bengaluru - 560068"},
    {"title": "Water supply disruption in Indiranagar for 3 days",
     "description": "No water supply for the past 3 days in Indiranagar 12th cross. Residents are dependent on water tankers.",
     "category": "water_supply", "priority": "high", "status": "in_progress",
     "ward_number": "Ward-9", "latitude": 12.9784, "longitude": 77.6408,
     "address": "12th Cross, Indiranagar, Bengaluru - 560038"},
    {"title": "Streetlight not working near Cubbon Park for 2 weeks",
     "description": "Multiple streetlights near the Cubbon Park entrance are non-functional, creating a safety hazard for pedestrians at night.",
     "category": "electricity", "priority": "medium", "status": "pending",
     "ward_number": "Ward-25", "latitude": 12.9763, "longitude": 77.5929,
     "address": "Cubbon Park Road, Bengaluru - 560001"},
    {"title": "Blocked storm drain causing flooding in residential area",
     "description": "Storm drain on 5th Main Road is completely blocked causing flooding in the area every time it rains.",
     "category": "drainage", "priority": "high", "status": "under_review",
     "ward_number": "Ward-42", "latitude": 12.9716, "longitude": 77.6412,
     "address": "5th Main Road, Koramangala, Bengaluru"},
    {"title": "Park benches broken and garden not maintained in JP Nagar",
     "description": "The public park in JP Nagar 6th Phase has broken benches, overgrown grass, and non-functional water fountains.",
     "category": "parks", "priority": "low", "status": "resolved",
     "ward_number": "Ward-55", "latitude": 12.9083, "longitude": 77.5947,
     "address": "JP Nagar 6th Phase, Bengaluru"},
]

SAMPLE_PROJECTS = [
    {"title": "BBMP Smart Road Widening Project - ORR Phase 2",
     "category": "roads", "status": "in_progress", "completion_percentage": 65.0,
     "estimated_cost": 12000000, "approved_budget": 12500000, "actual_cost": 8100000,
     "planned_start_date": "2024-01-15", "planned_end_date": "2024-12-31",
     "actual_start_date": "2024-01-20", "ward_number": "Ward-29",
     "latitude": 12.9352, "longitude": 77.6245, "dept_code": "ROADS",
     "contractor_name": "L&T Infrastructure Ltd", "delay_probability": 0.35},
    {"title": "Underground Water Supply Pipeline Replacement - Indiranagar",
     "category": "water_supply", "status": "in_progress", "completion_percentage": 40.0,
     "estimated_cost": 8000000, "approved_budget": 8500000, "actual_cost": 3800000,
     "planned_start_date": "2024-03-01", "planned_end_date": "2025-02-28",
     "actual_start_date": "2024-03-10", "ward_number": "Ward-9",
     "latitude": 12.9784, "longitude": 77.6408, "dept_code": "WATER",
     "contractor_name": "BWSSB Contractors", "delay_probability": 0.62},
    {"title": "Cubbon Park Rejuvenation and Lighting Upgrade",
     "category": "parks", "status": "planning", "completion_percentage": 0.0,
     "estimated_cost": 3500000, "approved_budget": None, "actual_cost": 0,
     "planned_start_date": "2025-01-01", "planned_end_date": "2025-06-30",
     "ward_number": "Ward-25", "latitude": 12.9763, "longitude": 77.5929,
     "dept_code": "PARKS", "delay_probability": 0.15},
    {"title": "Storm Water Drain Rehabilitation - Koramangala",
     "category": "drainage", "status": "tendering", "completion_percentage": 0.0,
     "estimated_cost": 5500000, "approved_budget": None, "actual_cost": 0,
     "planned_start_date": "2025-02-01", "planned_end_date": "2025-10-31",
     "ward_number": "Ward-42", "latitude": 12.9352, "longitude": 77.6244,
     "dept_code": "WATER", "delay_probability": 0.22},
    {"title": "LED Streetlight Installation - South Bengaluru",
     "category": "electricity", "status": "completed", "completion_percentage": 100.0,
     "estimated_cost": 6000000, "approved_budget": 6000000, "actual_cost": 5850000,
     "planned_start_date": "2024-01-01", "planned_end_date": "2024-06-30",
     "actual_start_date": "2024-01-05", "actual_end_date": "2024-06-15",
     "ward_number": "Ward-55", "latitude": 12.9083, "longitude": 77.5947,
     "dept_code": "ELEC", "delay_probability": 0.0},
]


async def seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        print("🌱 Seeding departments...")
        dept_map = {}
        for d in DEPARTMENTS:
            dept = Department(**d)
            session.add(dept)
            await session.flush()
            dept_map[d["code"]] = dept
            print(f"  ✓ {dept.name}")

        print("\n🌱 Seeding users...")
        user_map = {}
        for u in USERS:
            dept_code = u.pop("dept_code", None)
            password = u.pop("password")
            user = User(
                **u,
                hashed_password=security.hash_password(password),
                is_active=True,
                is_verified=True,
                department_id=dept_map[dept_code].id if dept_code else None,
            )
            session.add(user)
            await session.flush()
            user_map[u["email"]] = user
            print(f"  ✓ {user.full_name} [{user.role}]")

        # Set department heads
        dept_map["ROADS"].head_officer_id = user_map["engineer.roads@civilinc.gov.in"].id
        dept_map["WATER"].head_officer_id = user_map["engineer.water@civilinc.gov.in"].id
        await session.flush()

        print("\n🌱 Seeding complaints...")
        citizen = user_map["citizen1@example.com"]
        citizen2 = user_map["citizen2@example.com"]
        for i, c in enumerate(SAMPLE_COMPLAINTS):
            dept_code = {
                "roads": "ROADS", "water_supply": "WATER", "electricity": "ELEC",
                "drainage": "WATER", "parks": "PARKS", "sanitation": "SWM",
            }.get(c["category"], "ROADS")

            complaint = Complaint(
                **c,
                complaint_number=f"CMP-{str(i+1).zfill(7)}",
                citizen_id=citizen.id if i % 2 == 0 else citizen2.id,
                department_id=dept_map[dept_code].id,
                assigned_officer_id=user_map["engineer.roads@civilinc.gov.in"].id if dept_code == "ROADS" else None,
                source="web",
                ai_processed=False,
            )
            session.add(complaint)
            print(f"  ✓ {complaint.complaint_number}: {c['title'][:50]}")

        print("\n🌱 Seeding projects...")
        engineer = user_map["engineer.roads@civilinc.gov.in"]
        for p in SAMPLE_PROJECTS:
            dept_code = p.pop("dept_code")
            project = Project(
                **p,
                project_number=f"PRJ-{str(SAMPLE_PROJECTS.index(p)+1).zfill(6)}",
                department_id=dept_map[dept_code].id,
                project_manager_id=engineer.id,
                budget_utilized_pct=round((p.get("actual_cost", 0) / p.get("approved_budget", 1) * 100), 1)
                    if p.get("approved_budget") else 0,
                is_public=True,
            )
            session.add(project)
            print(f"  ✓ {project.project_number}: {p['title'][:50]}")

        print("\n🌱 Seeding forum thread...")
        thread = ForumThread(
            title="Monsoon Preparedness 2025 - All Department Coordination",
            body="This thread is for coordinating monsoon preparedness activities across all departments. Please update your drain clearing and road patching schedules.",
            category="infrastructure",
            author_id=user_map["commissioner@civilinc.gov.in"].id,
            is_pinned=True,
            is_announcement=True,
            tags=["monsoon", "coordination", "urgent"],
        )
        session.add(thread)

        await session.commit()
        print("\n✅ Seed data loaded successfully!")
        print("\n📋 Test Credentials:")
        print("  Commissioner : commissioner@civilinc.gov.in / Admin@1234")
        print("  Engineer     : engineer.roads@civilinc.gov.in / Engineer@1234")
        print("  Coordinator  : coordinator@civilinc.gov.in / Coord@1234")
        print("  Citizen      : citizen1@example.com / Citizen@1234")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
