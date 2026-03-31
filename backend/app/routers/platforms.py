from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.platform import Platform
from app.schemas.platform import PlatformCreate, PlatformOut

router = APIRouter(prefix="/platforms", tags=["platforms"])


@router.get("", response_model=list[PlatformOut])
async def list_platforms(
    db: AsyncSession = Depends(get_db), _=Depends(get_current_user)
):
    result = await db.execute(select(Platform))
    return result.scalars().all()


@router.post("", response_model=PlatformOut)
async def create_platform(
    req: PlatformCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    platform = Platform(**req.model_dump())
    db.add(platform)
    await db.commit()
    await db.refresh(platform)
    return platform
