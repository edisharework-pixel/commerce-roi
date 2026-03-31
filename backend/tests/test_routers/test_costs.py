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
async def test_create_and_list_categories(db_session, override_db):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await _get_auth_header(client)
        resp = await client.post(
            "/costs/categories",
            headers=headers,
            json={"name": "포장비", "type": "variable"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "포장비"
        assert data["type"] == "variable"

        resp = await client.get("/costs/categories", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_create_variable_cost(db_session, override_db):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await _get_auth_header(client)

        # Create product first
        await client.post(
            "/products",
            headers=headers,
            json={
                "name": "테스트상품",
                "sku": "TST-001",
                "base_cost": "10000",
                "category": "테스트",
            },
        )

        # Create category
        cat_resp = await client.post(
            "/costs/categories",
            headers=headers,
            json={"name": "포장비", "type": "variable"},
        )
        cat_id = cat_resp.json()["id"]

        # Create variable cost
        resp = await client.post(
            "/costs/variable",
            headers=headers,
            json={
                "product_id": 1,
                "category_id": cat_id,
                "amount": "500",
                "period_start": "2025-01-01",
                "period_end": "2025-01-31",
            },
        )
        assert resp.status_code == 200
        assert float(resp.json()["amount"]) == 500.0

        # List with filter
        resp = await client.get(
            "/costs/variable", headers=headers, params={"product_id": 1}
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_create_campaign_with_products(db_session, override_db):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await _get_auth_header(client)

        # Create product
        await client.post(
            "/products",
            headers=headers,
            json={
                "name": "테스트상품",
                "sku": "TST-001",
                "base_cost": "10000",
                "category": "테스트",
            },
        )

        resp = await client.post(
            "/costs/campaigns",
            headers=headers,
            json={
                "name": "봄 프로모션",
                "start_date": "2025-03-01",
                "end_date": "2025-03-31",
                "allocation_method": "equal",
                "product_ids": [1],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "봄 프로모션"
        assert data["allocation_method"] == "equal"

        resp = await client.get("/costs/campaigns", headers=headers)
        assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_create_marketing_cost(db_session, override_db):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await _get_auth_header(client)

        # Create category
        cat_resp = await client.post(
            "/costs/categories",
            headers=headers,
            json={"name": "광고비", "type": "marketing"},
        )
        cat_id = cat_resp.json()["id"]

        resp = await client.post(
            "/costs/marketing",
            headers=headers,
            json={
                "category_id": cat_id,
                "amount": "50000",
                "cost_date": "2025-03-15",
            },
        )
        assert resp.status_code == 200
        assert float(resp.json()["amount"]) == 50000.0

        resp = await client.get("/costs/marketing", headers=headers)
        assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_costs_requires_auth(db_session, override_db):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/costs/categories")
        assert resp.status_code in (401, 403)
