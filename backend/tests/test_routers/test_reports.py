from datetime import date
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.platform import Platform
from app.models.product import PlatformProduct, Product
from app.models.sales import SalesSummary
from app.models.upload import UploadHistory


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
async def test_profit_report(db_session, override_db):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await _get_auth_header(client)

        # Create platform
        platform = Platform(
            name="네이버 스마트스토어",
            type="마켓",
            fee_rate=5.5,
            vat_included=True,
        )
        db_session.add(platform)
        await db_session.commit()

        # Create product
        product = Product(
            name="바디트리머", sku="BT-001", base_cost=25000, category="미용"
        )
        db_session.add(product)
        await db_session.commit()

        # Create platform_product
        pp = PlatformProduct(
            product_id=product.id,
            platform_id=platform.id,
            platform_product_id="NV-100",
            platform_product_name="바디트리머",
            return_shipping_fee=5000,
            matched_by="manual",
        )
        db_session.add(pp)
        await db_session.commit()

        # Create upload history
        u = UploadHistory(
            platform_id=platform.id,
            data_type="sales_summary",
            file_name="t.csv",
            record_count=1,
            period_start=date(2026, 3, 1),
            period_end=date(2026, 3, 31),
        )
        db_session.add(u)
        await db_session.commit()

        # Create sales summary
        db_session.add(
            SalesSummary(
                platform_product_id=pp.id,
                period_start=date(2026, 3, 1),
                period_end=date(2026, 3, 31),
                gross_revenue=Decimal("5000000"),
                net_revenue=Decimal("4500000"),
                quantity=100,
                refund_amount=Decimal("300000"),
                refund_count=5,
                coupon_seller=Decimal("50000"),
                coupon_order=Decimal("30000"),
                upload_id=u.id,
            )
        )
        await db_session.commit()

        # Query report
        resp = await client.get(
            "/reports/profit",
            headers=headers,
            params={
                "product_id": product.id,
                "period_start": "2026-03-01",
                "period_end": "2026-03-31",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["product_id"] == product.id
        assert data["product_name"] == "바디트리머"
        assert len(data["platforms"]) == 1
        assert float(data["platforms"][0]["revenue"]) == 4500000.0


@pytest.mark.asyncio
async def test_unmatched_summary(db_session, override_db):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = await _get_auth_header(client)
        resp = await client.get("/reports/unmatched-summary", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["unmatched_sales"] == 0
        assert data["unmatched_ads"] == 0
