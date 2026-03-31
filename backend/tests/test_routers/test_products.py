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
async def test_create_and_list_products(db_session, override_db):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await _get_auth_header(client)
        resp = await client.post(
            "/products",
            headers=headers,
            json={
                "name": "\ubc14\ub514\ud2b8\ub9ac\uba38",
                "sku": "BT-001",
                "base_cost": "25000",
                "category": "\ubbf8\uc6a9",
            },
        )
        assert resp.status_code == 200
        resp = await client.get("/products", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_get_product_not_found(db_session, override_db):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await _get_auth_header(client)
        resp = await client.get("/products/999", headers=headers)
        assert resp.status_code == 404
