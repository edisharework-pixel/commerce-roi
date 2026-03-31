from datetime import date
from decimal import Decimal

import pytest

from app.models.platform import Platform
from app.models.product import PlatformProduct, Product
from app.models.sales import Order, SalesSummary
from app.models.upload import UploadHistory
from app.services.profit_calculator import ProfitCalculator


@pytest.fixture
async def profit_fixtures(db_session):
    pn = Platform(
        name="네이버 스마트스토어",
        type="마켓",
        fee_rate=5.5,
        vat_included=True,
    )
    pc = Platform(
        name="쿠팡",
        type="마켓",
        fee_rate=10.8,
        vat_included=False,
    )
    pg = Platform(
        name="지마켓",
        type="마켓",
        fee_rate=12.0,
        vat_included=False,
        site_identifier="G",
    )
    product = Product(
        name="바디트리머", sku="BT-001", base_cost=25000, category="미용"
    )
    db_session.add_all([pn, pc, pg, product])
    await db_session.commit()

    ppn = PlatformProduct(
        product_id=product.id,
        platform_id=pn.id,
        platform_product_id="NV-100",
        platform_product_name="바디트리머",
        return_shipping_fee=5000,
        matched_by="manual",
    )
    ppc = PlatformProduct(
        product_id=product.id,
        platform_id=pc.id,
        platform_product_id="CP-100",
        platform_product_name="바디트리머",
        matched_by="manual",
    )
    ppg = PlatformProduct(
        product_id=product.id,
        platform_id=pg.id,
        platform_product_id="GP-100",
        platform_product_name="바디트리머",
        site="G",
        matched_by="manual",
    )
    db_session.add_all([ppn, ppc, ppg])
    await db_session.commit()

    u = UploadHistory(
        platform_id=pn.id,
        data_type="sales_summary",
        file_name="t.csv",
        record_count=1,
        period_start=date(2026, 3, 1),
        period_end=date(2026, 3, 31),
    )
    db_session.add(u)
    await db_session.commit()

    # Naver sales
    db_session.add(
        SalesSummary(
            platform_product_id=ppn.id,
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

    u2 = UploadHistory(
        platform_id=pc.id,
        data_type="sales_summary",
        file_name="t2.csv",
        record_count=1,
        period_start=date(2026, 3, 1),
        period_end=date(2026, 3, 31),
    )
    db_session.add(u2)
    await db_session.commit()

    # Coupang sales
    db_session.add(
        SalesSummary(
            platform_product_id=ppc.id,
            period_start=date(2026, 3, 1),
            period_end=date(2026, 3, 31),
            gross_revenue=Decimal("3000000"),
            net_revenue=Decimal("2500000"),
            quantity=50,
            cancel_amount=Decimal("500000"),
            cancel_quantity=10,
            upload_id=u2.id,
        )
    )

    u3 = UploadHistory(
        platform_id=pg.id,
        data_type="order",
        file_name="t3.csv",
        record_count=2,
        period_start=date(2026, 3, 1),
        period_end=date(2026, 3, 31),
    )
    db_session.add(u3)
    await db_session.commit()

    # Gmarket orders
    db_session.add(
        Order(
            platform_product_id=ppg.id,
            order_date=date(2026, 3, 15),
            order_number="GM-001",
            quantity=2,
            sale_price=Decimal("45900"),
            status="배송완료",
            site="G",
            upload_id=u3.id,
        )
    )
    db_session.add(
        Order(
            platform_product_id=ppg.id,
            order_date=date(2026, 3, 16),
            order_number="GM-002",
            quantity=1,
            sale_price=Decimal("45900"),
            status="취소완료",
            site="G",
            upload_id=u3.id,
        )
    )
    await db_session.commit()
    return {"naver": pn, "coupang": pc, "gmarket": pg, "product": product}


@pytest.mark.asyncio
async def test_naver_profit(db_session, profit_fixtures):
    f = await profit_fixtures
    calc = ProfitCalculator(db_session)
    results = await calc.calculate(f["product"].id, date(2026, 3, 1), date(2026, 3, 31))
    nv = next(r for r in results if r.platform_name.startswith("네이버"))
    assert nv.revenue == Decimal("4500000")
    assert nv.cost_of_goods > 0
    assert nv.net_profit < nv.revenue


@pytest.mark.asyncio
async def test_coupang_profit(db_session, profit_fixtures):
    f = await profit_fixtures
    calc = ProfitCalculator(db_session)
    results = await calc.calculate(f["product"].id, date(2026, 3, 1), date(2026, 3, 31))
    cp = next(r for r in results if r.platform_name.startswith("쿠팡"))
    assert cp.revenue == Decimal("2500000")


@pytest.mark.asyncio
async def test_gmarket_profit(db_session, profit_fixtures):
    f = await profit_fixtures
    calc = ProfitCalculator(db_session)
    results = await calc.calculate(f["product"].id, date(2026, 3, 1), date(2026, 3, 31))
    gm = next(r for r in results if r.platform_name.startswith("지마켓"))
    assert gm.revenue == Decimal("91800")  # 2 * 45900
