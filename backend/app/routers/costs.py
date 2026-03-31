from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.cost import (
    Campaign,
    CampaignProduct,
    CostCategory,
    MarketingCost,
    VariableCost,
)
from app.schemas.cost import (
    CampaignCreate,
    CampaignOut,
    CostCategoryCreate,
    CostCategoryOut,
    MarketingCostCreate,
    MarketingCostOut,
    VariableCostCreate,
    VariableCostOut,
)

router = APIRouter(prefix="/costs", tags=["costs"])


# --- Cost Categories ---


@router.get("/categories", response_model=list[CostCategoryOut])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(CostCategory))
    return result.scalars().all()


@router.post("/categories", response_model=CostCategoryOut)
async def create_category(
    body: CostCategoryCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    cat = CostCategory(name=body.name, type=body.type)
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


# --- Variable Costs ---


@router.get("/variable", response_model=list[VariableCostOut])
async def list_variable_costs(
    product_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    stmt = select(VariableCost)
    if product_id:
        stmt = stmt.where(VariableCost.product_id == product_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/variable", response_model=VariableCostOut)
async def create_variable_cost(
    body: VariableCostCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    vc = VariableCost(
        product_id=body.product_id,
        category_id=body.category_id,
        amount=body.amount,
        period_start=body.period_start,
        period_end=body.period_end,
    )
    db.add(vc)
    await db.commit()
    await db.refresh(vc)
    return vc


# --- Campaigns ---


@router.get("/campaigns", response_model=list[CampaignOut])
async def list_campaigns(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(Campaign))
    return result.scalars().all()


@router.post("/campaigns", response_model=CampaignOut)
async def create_campaign(
    body: CampaignCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    campaign = Campaign(
        name=body.name,
        start_date=body.start_date,
        end_date=body.end_date,
        allocation_method=body.allocation_method,
    )
    db.add(campaign)
    await db.flush()
    for pid in body.product_ids:
        db.add(CampaignProduct(campaign_id=campaign.id, product_id=pid))
    await db.commit()
    await db.refresh(campaign)
    return campaign


# --- Marketing Costs ---


@router.get("/marketing", response_model=list[MarketingCostOut])
async def list_marketing_costs(
    campaign_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    stmt = select(MarketingCost)
    if campaign_id:
        stmt = stmt.where(MarketingCost.campaign_id == campaign_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/marketing", response_model=MarketingCostOut)
async def create_marketing_cost(
    body: MarketingCostCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    mc = MarketingCost(
        campaign_id=body.campaign_id,
        category_id=body.category_id,
        product_id=body.product_id,
        amount=body.amount,
        cost_date=body.cost_date,
    )
    db.add(mc)
    await db.commit()
    await db.refresh(mc)
    return mc
