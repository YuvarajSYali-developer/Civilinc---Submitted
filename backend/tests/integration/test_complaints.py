"""Integration tests for complaint endpoints."""
import pytest


@pytest.mark.asyncio
async def test_citizen_create_complaint(client, citizen_token):
    resp = await client.post(
        "/api/v1/complaints",
        headers={"Authorization": f"Bearer {citizen_token}"},
        json={
            "title": "Large pothole on main road causing accidents",
            "description": "There is a very large pothole on the main road that has caused multiple accidents this week.",
            "category": "roads",
            "address": "5th Main Road, Bengaluru",
            "ward_number": "Ward-1",
            "latitude": 12.9716,
            "longitude": 77.5946,
        }
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["complaint_number"].startswith("CMP-")
    assert data["status"] == "pending"
    assert data["category"] == "roads"


@pytest.mark.asyncio
async def test_citizen_only_sees_own_complaints(client, citizen_token, commissioner_token, db_session):
    # Create complaint as citizen
    await client.post(
        "/api/v1/complaints",
        headers={"Authorization": f"Bearer {citizen_token}"},
        json={
            "title": "Water supply disruption in my area",
            "description": "No water for three days in Indiranagar residential block.",
            "category": "water_supply",
        }
    )
    # Citizen sees their own
    citizen_resp = await client.get(
        "/api/v1/complaints",
        headers={"Authorization": f"Bearer {citizen_token}"}
    )
    assert citizen_resp.status_code == 200
    # Commissioner sees all
    comm_resp = await client.get(
        "/api/v1/complaints",
        headers={"Authorization": f"Bearer {commissioner_token}"}
    )
    assert comm_resp.status_code == 200


@pytest.mark.asyncio
async def test_complaint_feedback_requires_resolved_status(client, citizen_token):
    create_resp = await client.post(
        "/api/v1/complaints",
        headers={"Authorization": f"Bearer {citizen_token}"},
        json={
            "title": "Streetlight not working near park",
            "description": "Streetlight has been broken for two weeks causing safety hazard at night.",
            "category": "electricity",
        }
    )
    complaint_id = create_resp.json()["id"]
    feedback_resp = await client.post(
        f"/api/v1/complaints/{complaint_id}/feedback",
        headers={"Authorization": f"Bearer {citizen_token}"},
        json={"rating": 5, "feedback": "Very quick resolution"}
    )
    # Should fail — complaint not yet resolved
    assert feedback_resp.status_code == 400


@pytest.mark.asyncio
async def test_complaint_title_too_short(client, citizen_token):
    resp = await client.post(
        "/api/v1/complaints",
        headers={"Authorization": f"Bearer {citizen_token}"},
        json={
            "title": "Short",
            "description": "This description is long enough to pass validation minimum requirements.",
            "category": "roads",
        }
    )
    assert resp.status_code == 422
