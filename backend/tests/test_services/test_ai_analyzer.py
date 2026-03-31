from datetime import date
from decimal import Decimal
import pytest
from app.models.ad import AdData
from app.models.platform import Platform
from app.models.product import PlatformProduct, Product
from app.services.ai_analyzer import AIAdAnalyzer


@pytest.fixture
async def ai_fixtures(db_session):
    platform = Platform(name="네이버 검색광고", type="외부광고", fee_rate=0, vat_included=True)
    product = Product(name="바디트리머", sku="AI-001", base_cost=25000, category="미용")
    db_session.add_all([platform, product])
    await db_session.commit()

    pp = PlatformProduct(product_id=product.id, platform_id=platform.id,
        platform_product_id="NV-AD-100", platform_product_name="바디트리머", matched_by="manual")
    db_session.add(pp)
    await db_session.commit()

    db_session.add(AdData(platform_id=platform.id, platform_product_id=pp.id,
        campaign_name="◆바디트리머", spend=Decimal("50000"), impressions=10000,
        clicks=500, direct_conversions=15, direct_revenue=Decimal("750000"),
        ad_date=date(2026, 3, 15), match_status="matched"))
    await db_session.commit()
    return {"platform": platform, "product": product}


@pytest.mark.asyncio
async def test_analyze_generates_suggestions(db_session, ai_fixtures):
    f = await ai_fixtures
    analyzer = AIAdAnalyzer(db_session)
    result = await analyzer.analyze_product_ads(f["product"].id, date(2026, 3, 1), date(2026, 3, 31))
    assert "suggestions" in result
    assert len(result["suggestions"]) > 0
    assert "analysis_result" in result


@pytest.mark.asyncio
async def test_analyze_no_data(db_session):
    product = Product(name="빈상품", sku="EMPTY-001", base_cost=10000, category="기타")
    db_session.add(product)
    await db_session.commit()
    analyzer = AIAdAnalyzer(db_session)
    result = await analyzer.analyze_product_ads(product.id, date(2026, 3, 1), date(2026, 3, 31))
    assert "분석할 광고 데이터가 없습니다" in result["suggestions"]
