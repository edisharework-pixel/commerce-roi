import pytest
from datetime import date
from sqlalchemy import select
from app.models.ad import AdAnalysisLog, AdCampaignProductMapping, AdData
from app.models.platform import Platform
from app.models.product import PlatformProduct, Product


async def _setup(db_session):
    platform = Platform(name="쿠팡", type="마켓", fee_rate=10.8, vat_included=False)
    product = Product(name="상품E", sku="SKU-E", base_cost=7000, category="전자")
    db_session.add_all([platform, product])
    await db_session.commit()

    pp = PlatformProduct(
        product_id=product.id,
        platform_id=platform.id,
        platform_product_id="CP-E",
        platform_product_name="쿠팡 상품E",
        matched_by="sku",
    )
    db_session.add(pp)
    await db_session.commit()
    return platform, product, pp


@pytest.mark.asyncio
async def test_create_ad_data(db_session):
    platform, product, pp = await _setup(db_session)
    ad = AdData(
        platform_id=platform.id,
        platform_product_id=pp.id,
        campaign_name="쿠팡 브랜드광고",
        keyword="무선청소기",
        spend=50000,
        impressions=10000,
        clicks=500,
        direct_conversions=20,
        direct_revenue=400000,
        ad_date=date(2024, 1, 10),
        match_status="matched",
        extended_metrics={"roas": 8.0},
    )
    db_session.add(ad)
    await db_session.commit()
    result = await db_session.execute(select(AdData))
    found = result.scalar_one()
    assert found.keyword == "무선청소기"
    assert found.extended_metrics == {"roas": 8.0}
    assert found.match_status == "matched"


@pytest.mark.asyncio
async def test_create_ad_campaign_product_mapping(db_session):
    platform, product, pp = await _setup(db_session)
    mapping = AdCampaignProductMapping(
        platform_id=platform.id,
        campaign_name="쿠팡 브랜드광고",
        product_id=product.id,
        allocation_method="revenue",
    )
    db_session.add(mapping)
    await db_session.commit()
    result = await db_session.execute(select(AdCampaignProductMapping))
    found = result.scalar_one()
    assert found.allocation_method == "revenue"
    assert found.created_at is not None


@pytest.mark.asyncio
async def test_create_ad_analysis_log(db_session):
    platform, product, pp = await _setup(db_session)
    log = AdAnalysisLog(
        product_id=product.id,
        period_start=date(2024, 1, 1),
        period_end=date(2024, 1, 31),
        analysis_result={"roas": 5.2, "cpc": 100},
        suggestions="CPC를 낮추고 키워드를 확장하세요.",
    )
    db_session.add(log)
    await db_session.commit()
    result = await db_session.execute(select(AdAnalysisLog))
    found = result.scalar_one()
    assert found.analysis_result["roas"] == 5.2
    assert "키워드" in found.suggestions
