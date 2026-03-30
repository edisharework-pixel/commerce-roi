import pytest
from sqlalchemy import select
from app.models.platform import Platform


@pytest.mark.asyncio
async def test_create_platform(db_session):
    platform = Platform(name="쿠팡", type="마켓", fee_rate=10.8, vat_included=False)
    db_session.add(platform)
    await db_session.commit()
    result = await db_session.execute(select(Platform).where(Platform.name == "쿠팡"))
    found = result.scalar_one()
    assert found.name == "쿠팡"
    assert found.fee_rate == 10.8


@pytest.mark.asyncio
async def test_create_gmarket_platform(db_session):
    platform = Platform(
        name="지마켓",
        type="마켓",
        fee_rate=12.0,
        vat_included=False,
        site_identifier="G",
        seller_id="itholic",
    )
    db_session.add(platform)
    await db_session.commit()
    result = await db_session.execute(
        select(Platform).where(Platform.site_identifier == "G")
    )
    found = result.scalar_one()
    assert found.seller_id == "itholic"
