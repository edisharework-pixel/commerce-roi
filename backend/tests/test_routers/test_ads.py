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


async def _create_platform_and_product(client, headers):
    """Helper to create a platform and product for mapping tests."""
    await client.post(
        "/platforms",
        headers=headers,
        json={
            "name": "네이버 스마트스토어",
            "type": "marketplace",
            "fee_rate": "5.5",
        },
    )
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


@pytest.mark.asyncio
async def test_list_ads_empty(db_session, override_db):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await _get_auth_header(client)
        resp = await client.get("/ads", headers=headers)
        assert resp.status_code == 200
        assert resp.json() == []


@pytest.mark.asyncio
async def test_list_unmatched_ads_empty(db_session, override_db):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await _get_auth_header(client)
        resp = await client.get("/ads/unmatched", headers=headers)
        assert resp.status_code == 200
        assert resp.json() == []


@pytest.mark.asyncio
async def test_create_and_list_campaign_mapping(db_session, override_db):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await _get_auth_header(client)
        await _create_platform_and_product(client, headers)

        resp = await client.post(
            "/ads/campaign-mapping",
            headers=headers,
            json={
                "platform_id": 1,
                "campaign_name": "봄 캠페인",
                "product_id": 1,
                "allocation_method": "single",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["campaign_name"] == "봄 캠페인"
        assert data["allocation_method"] == "single"

        resp = await client.get("/ads/campaign-mapping", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_delete_campaign_mapping(db_session, override_db):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await _get_auth_header(client)
        await _create_platform_and_product(client, headers)

        resp = await client.post(
            "/ads/campaign-mapping",
            headers=headers,
            json={
                "platform_id": 1,
                "campaign_name": "삭제 캠페인",
                "product_id": 1,
            },
        )
        mapping_id = resp.json()["id"]

        resp = await client.delete(
            f"/ads/campaign-mapping/{mapping_id}", headers=headers
        )
        assert resp.status_code == 204

        resp = await client.get("/ads/campaign-mapping", headers=headers)
        assert len(resp.json()) == 0


@pytest.mark.asyncio
async def test_delete_mapping_not_found(db_session, override_db):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await _get_auth_header(client)
        resp = await client.delete("/ads/campaign-mapping/999", headers=headers)
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_ads_requires_auth(db_session, override_db):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/ads")
        assert resp.status_code in (401, 403)
