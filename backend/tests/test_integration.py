import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_full_flow(db_session, override_db):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Register + login
        await client.post(
            "/auth/register",
            json={"username": "admin", "password": "test1234", "role": "admin"},
        )
        resp = await client.post(
            "/auth/login",
            json={"username": "admin", "password": "test1234"},
        )
        headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}

        # Create product
        resp = await client.post(
            "/products",
            headers=headers,
            json={
                "name": "바디트리머",
                "sku": "BT-001",
                "base_cost": "25000",
                "category": "미용",
            },
        )
        assert resp.status_code == 200
        product_id = resp.json()["id"]

        # Create platform
        resp = await client.post(
            "/platforms",
            headers=headers,
            json={
                "name": "테스트마켓",
                "type": "마켓",
                "fee_rate": "10.0",
                "vat_included": False,
            },
        )
        assert resp.status_code == 200

        # Create cost category
        resp = await client.post(
            "/costs/categories",
            headers=headers,
            json={"name": "테스트비용", "type": "변동비"},
        )
        assert resp.status_code == 200

        # Health check
        resp = await client.get("/health")
        assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_cors_headers(db_session, override_db):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.status_code == 200
