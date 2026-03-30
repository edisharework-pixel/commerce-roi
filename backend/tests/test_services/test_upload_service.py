import io
from datetime import date

import pytest
from sqlalchemy import select

from app.models.platform import Platform
from app.models.product import PlatformProduct, Product
from app.models.sales import Order, SalesSummary
from app.models.upload import UploadHistory
from app.services.upload_service import UploadService


@pytest.fixture
async def upload_fixtures(db_session):
    platform_gm = Platform(
        name="지마켓",
        type="마켓",
        fee_rate=12.0,
        vat_included=False,
        site_identifier="G",
        seller_id="itholic",
    )
    platform_nv = Platform(
        name="네이버 스마트스토어",
        type="마켓",
        fee_rate=5.5,
        vat_included=True,
    )
    product = Product(
        name="바디트리머 프로", sku="BT-PRO", base_cost=25000, category="미용"
    )
    db_session.add_all([platform_gm, platform_nv, product])
    await db_session.commit()

    pp_gm = PlatformProduct(
        product_id=product.id,
        platform_id=platform_gm.id,
        platform_product_id="GP-100",
        platform_product_name="바디트리머 프로",
        site="G",
        matched_by="manual",
    )
    pp_nv = PlatformProduct(
        product_id=product.id,
        platform_id=platform_nv.id,
        platform_product_id="12345678",
        platform_product_name="바디트리머 프로 남성용",
        matched_by="manual",
    )
    db_session.add_all([pp_gm, pp_nv])
    await db_session.commit()
    return {"gmarket": platform_gm, "naver": platform_nv, "product": product}


@pytest.mark.asyncio
async def test_upload_gmarket_orders(db_session, upload_fixtures):
    fixtures = await upload_fixtures
    csv = "주문번호,결제일,상품번호,상품명,수량,구매금액,진행상태,판매아이디\nGM-001,2026-03-15,GP-100,바디트리머 프로,1,45900,배송완료,지마켓(itholic)"
    service = UploadService(db_session)
    result = await service.process_upload(
        file=io.BytesIO(csv.encode("utf-8-sig")),
        file_type="csv",
        platform_id=fixtures["gmarket"].id,
        data_type="order",
        period_start=date(2026, 3, 1),
        period_end=date(2026, 3, 31),
        file_name="gmarket.csv",
    )
    assert result.record_count == 1 and result.matched_count == 1
    orders = (await db_session.execute(select(Order))).scalars().all()
    assert len(orders) == 1 and orders[0].order_number == "GM-001"


@pytest.mark.asyncio
async def test_upload_naver_sales(db_session, upload_fixtures):
    fixtures = await upload_fixtures
    csv = "상품번호,상품명,결제상품수량,결제금액,환불금액,환불수량,상품쿠폰합계,주문쿠폰합계\n12345678,바디트리머 프로 남성용,150,4500000,300000,5,50000,30000"
    service = UploadService(db_session)
    result = await service.process_upload(
        file=io.BytesIO(csv.encode("utf-8-sig")),
        file_type="csv",
        platform_id=fixtures["naver"].id,
        data_type="sales_summary",
        period_start=date(2026, 3, 1),
        period_end=date(2026, 3, 31),
        file_name="naver.csv",
    )
    assert result.record_count == 1 and result.matched_count == 1
    summaries = (await db_session.execute(select(SalesSummary))).scalars().all()
    assert len(summaries) == 1 and summaries[0].net_revenue == 4500000
