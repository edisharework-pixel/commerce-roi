import pytest

from app.matching.product_matcher import ProductMatcher
from app.models.platform import Platform
from app.models.product import PlatformProduct, Product


@pytest.fixture
async def matcher_fixtures(db_session):
    platform = Platform(
        name="쿠팡", type="마켓", fee_rate=10.8, vat_included=False
    )
    product = Product(
        name="바디트리머 프로", sku="BT-PRO", base_cost=25000, category="미용"
    )
    db_session.add_all([platform, product])
    await db_session.commit()
    pp = PlatformProduct(
        product_id=product.id,
        platform_id=platform.id,
        platform_product_id="CP-100",
        platform_product_name="바디트리머 프로 남성용",
        seller_product_code="BT-PRO-001",
        matched_by="manual",
    )
    db_session.add(pp)
    await db_session.commit()
    return platform, product, pp


@pytest.mark.asyncio
async def test_exact_match(db_session, matcher_fixtures):
    platform, product, pp = await matcher_fixtures
    matcher = ProductMatcher(db_session)
    result = await matcher.match(
        platform_id=platform.id,
        platform_product_id="CP-100",
        product_name="바디트리머",
    )
    assert result.matched and result.method == "exact" and result.confidence == 100.0


@pytest.mark.asyncio
async def test_seller_code_match(db_session, matcher_fixtures):
    platform, _, _ = await matcher_fixtures
    matcher = ProductMatcher(db_session)
    result = await matcher.match(
        platform_id=platform.id,
        platform_product_id="NEW-999",
        product_name="바디트리머",
        seller_product_code="BT-PRO-001",
    )
    assert result.matched and result.method == "seller_code"


@pytest.mark.asyncio
async def test_no_match(db_session, matcher_fixtures):
    platform, _, _ = await matcher_fixtures
    matcher = ProductMatcher(db_session)
    result = await matcher.match(
        platform_id=platform.id,
        platform_product_id="UNKNOWN",
        product_name="완전히 다른 상품명",
    )
    assert not result.matched and result.method == "failed"
