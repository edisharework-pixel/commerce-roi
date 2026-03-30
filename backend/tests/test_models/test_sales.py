import pytest
from datetime import date
from sqlalchemy import select
from app.models.platform import Platform
from app.models.product import PlatformProduct, Product
from app.models.upload import UploadHistory
from app.models.sales import Order, SalesSummary, Settlement


async def _create_prerequisites(db_session):
    """Create platform, product, platform_product, and upload_history for FK refs."""
    platform = Platform(name="쿠팡", type="마켓", fee_rate=10.8, vat_included=False)
    product = Product(name="상품X", sku="SKU-X", base_cost=5000, category="생활")
    db_session.add_all([platform, product])
    await db_session.commit()

    pp = PlatformProduct(
        product_id=product.id,
        platform_id=platform.id,
        platform_product_id="CP001",
        platform_product_name="쿠팡 상품X",
        matched_by="sku",
    )
    db_session.add(pp)
    await db_session.commit()

    upload = UploadHistory(
        platform_id=platform.id,
        data_type="sales",
        file_name="sales_202401.xlsx",
        record_count=100,
        period_start=date(2024, 1, 1),
        period_end=date(2024, 1, 31),
    )
    db_session.add(upload)
    await db_session.commit()

    return platform, product, pp, upload


@pytest.mark.asyncio
async def test_create_sales_summary(db_session):
    platform, product, pp, upload = await _create_prerequisites(db_session)
    summary = SalesSummary(
        platform_product_id=pp.id,
        period_start=date(2024, 1, 1),
        period_end=date(2024, 1, 31),
        gross_revenue=1000000,
        net_revenue=900000,
        quantity=50,
        coupon_seller=5000,
        coupon_order=3000,
        upload_id=upload.id,
    )
    db_session.add(summary)
    await db_session.commit()
    result = await db_session.execute(select(SalesSummary))
    found = result.scalar_one()
    assert found.gross_revenue == 1000000
    assert found.coupon_seller == 5000


@pytest.mark.asyncio
async def test_create_order_with_status_and_site(db_session):
    platform, product, pp, upload = await _create_prerequisites(db_session)
    order = Order(
        platform_product_id=pp.id,
        order_date=date(2024, 1, 15),
        order_number="ORD-001",
        quantity=2,
        sale_price=20000,
        status="배송완료",
        site="G",
        upload_id=upload.id,
    )
    db_session.add(order)
    await db_session.commit()
    result = await db_session.execute(
        select(Order).where(Order.order_number == "ORD-001")
    )
    found = result.scalar_one()
    assert found.status == "배송완료"
    assert found.site == "G"
    assert found.last_updated is not None


@pytest.mark.asyncio
async def test_create_settlement(db_session):
    platform = Platform(name="네이버", type="스마트스토어", fee_rate=5.5, vat_included=True)
    db_session.add(platform)
    await db_session.commit()

    settlement = Settlement(
        platform_id=platform.id,
        period_start=date(2024, 1, 1),
        period_end=date(2024, 1, 31),
        expected_amount=500000,
        actual_amount=498000,
        status="confirmed",
    )
    db_session.add(settlement)
    await db_session.commit()
    result = await db_session.execute(select(Settlement))
    found = result.scalar_one()
    assert found.expected_amount == 500000
    assert found.status == "confirmed"
