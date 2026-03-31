from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.event import ChangeEvent, EventType
from app.models.user import User
from app.schemas.event import (
    ChangeEventCreate,
    ChangeEventOut,
    EventTypeCreate,
    EventTypeOut,
)

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/types", response_model=list[EventTypeOut])
async def list_event_types(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(EventType))
    return result.scalars().all()


@router.post("/types", response_model=EventTypeOut)
async def create_event_type(
    body: EventTypeCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    et = EventType(name=body.name, is_default=False, created_by=user.id)
    db.add(et)
    await db.commit()
    await db.refresh(et)
    return et


@router.get("", response_model=list[ChangeEventOut])
async def list_events(
    product_id: int | None = None,
    platform_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    stmt = select(ChangeEvent)
    if product_id:
        stmt = stmt.where(ChangeEvent.product_id == product_id)
    if platform_id:
        stmt = stmt.where(ChangeEvent.platform_id == platform_id)
    if date_from:
        stmt = stmt.where(ChangeEvent.event_date >= date_from)
    if date_to:
        stmt = stmt.where(ChangeEvent.event_date <= date_to)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=ChangeEventOut)
async def create_event(
    body: ChangeEventCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    event = ChangeEvent(
        event_type_id=body.event_type_id,
        product_id=body.product_id,
        platform_id=body.platform_id,
        description=body.description,
        change_details=body.change_details,
        event_date=body.event_date,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


@router.get("/{event_id}", response_model=ChangeEventOut)
async def get_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(
        select(ChangeEvent).where(ChangeEvent.id == event_id)
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
