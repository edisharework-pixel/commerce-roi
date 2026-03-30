import pytest
from datetime import date
from sqlalchemy import select
from app.models.cost import (
    Campaign,
    CampaignProduct,
    CostCategory,
    MarketingCost,
    VariableCost,
)
from app.models.product import Product


@pytest.mark.asyncio
async def test_create_cost_category(db_session):
    cat = CostCategory(name="포장비", type="variable")
    db_session.add(cat)
    await db_session.commit()
    result = await db_session.execute(select(CostCategory))
    found = result.scalar_one()
    assert found.name == "포장비"
    assert found.type == "variable"


@pytest.mark.asyncio
async def test_create_variable_cost(db_session):
    product = Product(name="상품C", sku="SKU-C", base_cost=3000, category="식품")
    cat = CostCategory(name="배송비", type="variable")
    db_session.add_all([product, cat])
    await db_session.commit()

    vc = VariableCost(
        product_id=product.id,
        category_id=cat.id,
        amount=2500,
        period_start=date(2024, 1, 1),
        period_end=date(2024, 1, 31),
    )
    db_session.add(vc)
    await db_session.commit()
    result = await db_session.execute(select(VariableCost))
    found = result.scalar_one()
    assert found.amount == 2500


@pytest.mark.asyncio
async def test_create_campaign_and_marketing_cost(db_session):
    product = Product(name="상품D", sku="SKU-D", base_cost=8000, category="뷰티")
    cat = CostCategory(name="광고비", type="marketing")
    db_session.add_all([product, cat])
    await db_session.commit()

    campaign = Campaign(
        name="신년 프로모션",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 15),
        allocation_method="equal",
    )
    db_session.add(campaign)
    await db_session.commit()

    cp = CampaignProduct(campaign_id=campaign.id, product_id=product.id)
    mc = MarketingCost(
        campaign_id=campaign.id,
        category_id=cat.id,
        product_id=product.id,
        amount=50000,
        cost_date=date(2024, 1, 5),
    )
    db_session.add_all([cp, mc])
    await db_session.commit()

    result = await db_session.execute(select(MarketingCost))
    found = result.scalar_one()
    assert found.amount == 50000

    result2 = await db_session.execute(select(CampaignProduct))
    found2 = result2.scalar_one()
    assert found2.campaign_id == campaign.id
