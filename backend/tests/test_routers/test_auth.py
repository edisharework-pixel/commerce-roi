import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_register_user(db_session, override_db):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/auth/register",
            json={"username": "admin", "password": "test1234", "role": "admin"},
        )
        assert resp.status_code == 200
        assert resp.json()["username"] == "admin"


@pytest.mark.asyncio
async def test_login_returns_token(db_session, override_db):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post(
            "/auth/register",
            json={"username": "admin", "password": "test1234", "role": "admin"},
        )
        resp = await client.post(
            "/auth/login",
            json={"username": "admin", "password": "test1234"},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_wrong_password(db_session, override_db):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post(
            "/auth/register",
            json={"username": "admin", "password": "test1234", "role": "admin"},
        )
        resp = await client.post(
            "/auth/login",
            json={"username": "admin", "password": "wrongpass"},
        )
        assert resp.status_code == 401
