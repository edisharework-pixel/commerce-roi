from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.ad import AdCampaignProductMapping, AdData
from app.schemas.ad import AdCampaignMappingCreate, AdCampaignMappingOut, AdDataOut

router = APIRouter(prefix="/ads", tags=["ads"])


@router.get("", response_model=list[AdDataOut])
async def list_ads(
    platform_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    stmt = select(AdData)
    if platform_id:
        stmt = stmt.where(AdData.platform_id == platform_id)
    if date_from:
        stmt = stmt.where(AdData.ad_date >= date_from)
    if date_to:
        stmt = stmt.where(AdData.ad_date <= date_to)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/unmatched", response_model=list[AdDataOut])
async def list_unmatched_ads(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    stmt = select(AdData).where(AdData.match_status != "matched")
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/campaign-mapping", response_model=list[AdCampaignMappingOut])
async def list_campaign_mappings(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(AdCampaignProductMapping))
    return result.scalars().all()


@router.post("/campaign-mapping", response_model=AdCampaignMappingOut)
async def create_campaign_mapping(
    body: AdCampaignMappingCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    mapping = AdCampaignProductMapping(
        platform_id=body.platform_id,
        campaign_name=body.campaign_name,
        product_id=body.product_id,
        allocation_method=body.allocation_method,
    )
    db.add(mapping)
    await db.commit()
    await db.refresh(mapping)
    return mapping


@router.delete("/campaign-mapping/{mapping_id}", status_code=204)
async def delete_campaign_mapping(
    mapping_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(
        select(AdCampaignProductMapping).where(
            AdCampaignProductMapping.id == mapping_id
        )
    )
    mapping = result.scalar_one_or_none()
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    await db.delete(mapping)
    await db.commit()
