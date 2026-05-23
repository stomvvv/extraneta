"""
Integration tests for auth endpoints.
These tests require a running PostgreSQL instance (use docker-compose).
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.mark.anyio
async def test_register_and_login(client: AsyncClient):
    # Register
    resp = await client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "securepassword",
        "full_name": "Test User",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data

    # Login with same credentials
    resp2 = await client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "securepassword",
    })
    assert resp2.status_code == 200
    assert "access_token" in resp2.json()


@pytest.mark.anyio
async def test_login_wrong_password(client: AsyncClient):
    await client.post("/api/auth/register", json={
        "email": "user2@example.com",
        "password": "correctpassword",
        "full_name": "User 2",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "user2@example.com",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_get_me(client: AsyncClient):
    reg = await client.post("/api/auth/register", json={
        "email": "me@example.com",
        "password": "password123",
        "full_name": "Me User",
    })
    token = reg.json()["access_token"]
    resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


@pytest.mark.anyio
async def test_refresh_token(client: AsyncClient):
    reg = await client.post("/api/auth/register", json={
        "email": "refresh@example.com",
        "password": "password123",
        "full_name": "Refresh User",
    })
    refresh_token = reg.json()["refresh_token"]
    resp = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()
