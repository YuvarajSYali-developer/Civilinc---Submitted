"""Integration tests for authentication endpoints."""
import pytest


@pytest.mark.asyncio
async def test_register_citizen(client):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "newcitizen@test.com",
        "password": "Test@1234",
        "full_name": "New Citizen",
        "ward_number": "Ward-5",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "newcitizen@test.com"
    assert data["role"] == "citizen"


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    payload = {"email": "dup@test.com", "password": "Test@1234", "full_name": "Dup User"}
    await client.post("/api/v1/auth/register", json=payload)
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client, db_session):
    # Register first
    await client.post("/api/v1/auth/register", json={
        "email": "logintest@test.com",
        "password": "Login@1234",
        "full_name": "Login Test",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "logintest@test.com",
        "password": "Login@1234",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/api/v1/auth/register", json={
        "email": "wrongpass@test.com",
        "password": "Correct@1234",
        "full_name": "Wrong Pass User",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "wrongpass@test.com",
        "password": "Wrong@1234",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client, commissioner_token):
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {commissioner_token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "comm_" in data["email"] or "commissioner" in data["email"]
    assert data["role"] == "commissioner"


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_health_check(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"
