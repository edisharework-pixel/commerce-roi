import pytest
from sqlalchemy import select
from app.models.cost import CostCategory
from app.models.event import EventType
from app.models.platform import Platform
from scripts.seed import seed_data


@pytest.mark.asyncio
async def test_seed_creates_platforms(db_session):
    await seed_data(db_session)
    result = await db_session.execute(select(Platform))
    platforms = result.scalars().all()
    names = {p.name for p in platforms}
    assert "쿠팡" in names
    assert "네이버 스마트스토어" in names
    assert "지마켓" in names
    assert "옥션" in names


@pytest.mark.asyncio
async def test_seed_creates_event_types(db_session):
    await seed_data(db_session)
    result = await db_session.execute(select(EventType).where(EventType.is_default.is_(True)))
    event_types = result.scalars().all()
    names = {et.name for et in event_types}
    assert "판매가 수정" in names
    assert "쿠폰 적용" in names
    assert "목표 ROAS 변경" in names
    assert "광고 예산 변경" in names


@pytest.mark.asyncio
async def test_seed_creates_cost_categories(db_session):
    await seed_data(db_session)
    result = await db_session.execute(select(CostCategory))
    categories = result.scalars().all()
    names = {c.name for c in categories}
    assert "인플루언서 비용" in names
    assert "촬영비" in names


@pytest.mark.asyncio
async def test_seed_is_idempotent(db_session):
    await seed_data(db_session)
    await seed_data(db_session)
    result = await db_session.execute(select(Platform))
    platforms = result.scalars().all()
    name_counts = {}
    for p in platforms:
        name_counts[p.name] = name_counts.get(p.name, 0) + 1
    assert all(count == 1 for count in name_counts.values())
