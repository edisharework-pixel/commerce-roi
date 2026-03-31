import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


async def _get_auth_header(client):
    await client.post(
        "/auth/register",
        json={"username": "admin", "password": "test1234", "role": "admin"},
    )
    resp = await client.post(
        "/auth/login",
        json={"username": "admin", "password": "test1234"},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.mark.asyncio
async def test_list_platforms(db_session, override_db):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await _get_auth_header(client)
        resp = await client.get("/platforms", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_create_platform(db_session, override_db):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await _get_auth_header(client)
        resp = await client.post(
            "/platforms",
            headers=headers,
            json={
                "name": "\ud14c\uc2a4\ud2b8\ub9c8\ucf13",
                "type": "\ub9c8\ucf13",
                "fee_rate": "5.5",
                "vat_included": False,
            },
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "\ud14c\uc2a4\ud2b8\ub9c8\ucf13"
