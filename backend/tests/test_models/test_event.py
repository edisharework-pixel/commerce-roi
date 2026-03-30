import pytest
from datetime import date
from sqlalchemy import select
from app.models.event import ChangeEvent, EventType
from app.models.platform import Platform
from app.models.product import Product
from app.models.user import User


@pytest.mark.asyncio
async def test_create_event_type(db_session):
    et = EventType(name="가격변경", is_default=True)
    db_session.add(et)
    await db_session.commit()
    result = await db_session.execute(select(EventType))
    found = result.scalar_one()
    assert found.name == "가격변경"
    assert found.is_default is True


@pytest.mark.asyncio
async def test_create_event_type_with_user(db_session):
    user = User(username="admin", password_hash="hash", role="admin")
    db_session.add(user)
    await db_session.commit()

    et = EventType(name="커스텀 이벤트", is_default=False, created_by=user.id)
    db_session.add(et)
    await db_session.commit()
    result = await db_session.execute(
        select(EventType).where(EventType.created_by == user.id)
    )
    found = result.scalar_one()
    assert found.name == "커스텀 이벤트"


@pytest.mark.asyncio
async def test_create_change_event(db_session):
    product = Product(name="상품F", sku="SKU-F", base_cost=12000, category="가전")
    platform = Platform(name="쿠팡", type="마켓", fee_rate=10.8, vat_included=False)
    et = EventType(name="수수료변경", is_default=True)
    db_session.add_all([product, platform, et])
    await db_session.commit()

    event = ChangeEvent(
        event_type_id=et.id,
        product_id=product.id,
        platform_id=platform.id,
        description="쿠팡 수수료율 10.8% -> 11.0% 변경",
        change_details={"old_fee_rate": 10.8, "new_fee_rate": 11.0},
        event_date=date(2024, 2, 1),
    )
    db_session.add(event)
    await db_session.commit()
    result = await db_session.execute(select(ChangeEvent))
    found = result.scalar_one()
    assert found.change_details["new_fee_rate"] == 11.0
    assert found.created_at is not None
