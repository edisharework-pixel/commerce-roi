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
async def test_create_and_list_event_types(db_session, override_db):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await _get_auth_header(client)
        resp = await client.post(
            "/events/types",
            headers=headers,
            json={"name": "가격 변경"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "가격 변경"
        assert data["is_default"] is False

        resp = await client.get("/events/types", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_create_and_list_events(db_session, override_db):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await _get_auth_header(client)

        # Create event type
        et_resp = await client.post(
            "/events/types",
            headers=headers,
            json={"name": "가격 변경"},
        )
        et_id = et_resp.json()["id"]

        # Create event
        resp = await client.post(
            "/events",
            headers=headers,
            json={
                "event_type_id": et_id,
                "description": "판매가 10% 인상",
                "change_details": {"old_price": 10000, "new_price": 11000},
                "event_date": "2025-03-15",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["description"] == "판매가 10% 인상"
        assert data["change_details"]["new_price"] == 11000

        # List events
        resp = await client.get("/events", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_get_event_detail(db_session, override_db):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await _get_auth_header(client)

        et_resp = await client.post(
            "/events/types",
            headers=headers,
            json={"name": "재고 변동"},
        )
        et_id = et_resp.json()["id"]

        create_resp = await client.post(
            "/events",
            headers=headers,
            json={
                "event_type_id": et_id,
                "description": "재고 소진",
                "change_details": {"before": 100, "after": 0},
                "event_date": "2025-03-20",
            },
        )
        event_id = create_resp.json()["id"]

        resp = await client.get(f"/events/{event_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["description"] == "재고 소진"


@pytest.mark.asyncio
async def test_get_event_not_found(db_session, override_db):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await _get_auth_header(client)
        resp = await client.get("/events/999", headers=headers)
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_events_with_filters(db_session, override_db):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await _get_auth_header(client)

        et_resp = await client.post(
            "/events/types",
            headers=headers,
            json={"name": "테스트"},
        )
        et_id = et_resp.json()["id"]

        await client.post(
            "/events",
            headers=headers,
            json={
                "event_type_id": et_id,
                "description": "이벤트1",
                "change_details": {},
                "event_date": "2025-03-10",
            },
        )

        # Filter by date range
        resp = await client.get(
            "/events",
            headers=headers,
            params={"date_from": "2025-03-01", "date_to": "2025-03-31"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        # Filter outside range
        resp = await client.get(
            "/events",
            headers=headers,
            params={"date_from": "2025-04-01"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 0


@pytest.mark.asyncio
async def test_events_requires_auth(db_session, override_db):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/events")
        assert resp.status_code in (401, 403)
