from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.product import PlatformProduct, Product
from app.schemas.product import (
    PlatformProductOut,
    ProductCreate,
    ProductOut,
    UnmatchedProductOut,
)

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductOut])
async def list_products(
    db: AsyncSession = Depends(get_db), _=Depends(get_current_user)
):
    result = await db.execute(select(Product))
    return result.scalars().all()


@router.post("", response_model=ProductOut)
async def create_product(
    req: ProductCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    product = Product(**req.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/{product_id}/platform-products", response_model=list[PlatformProductOut])
async def list_platform_products(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(
        select(PlatformProduct).where(PlatformProduct.product_id == product_id)
    )
    return result.scalars().all()


@router.get("/unmatched/list", response_model=list[UnmatchedProductOut])
async def list_unmatched(
    db: AsyncSession = Depends(get_db), _=Depends(get_current_user)
):
    result = await db.execute(
        select(PlatformProduct).where(PlatformProduct.matched_by == "failed")
    )
    return result.scalars().all()
