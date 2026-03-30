from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.cost import CostCategory
from app.models.event import EventType
from app.models.platform import Platform


async def _seed_if_empty(session: AsyncSession, model, items: list[dict]):
    result = await session.execute(select(model))
    if result.scalars().first() is not None:
        return
    for item in items:
        session.add(model(**item))
    await session.commit()


async def seed_data(session: AsyncSession):
    await _seed_if_empty(session, Platform, [
        {"name": "쿠팡", "type": "마켓", "fee_rate": 10.8, "vat_included": False},
        {"name": "네이버 스마트스토어", "type": "마켓", "fee_rate": 5.5, "vat_included": True},
        {"name": "지마켓", "type": "마켓", "fee_rate": 12.0, "vat_included": False, "site_identifier": "G", "seller_id": "itholic"},
        {"name": "옥션", "type": "마켓", "fee_rate": 12.0, "vat_included": False, "site_identifier": "A", "seller_id": "itemholic"},
        {"name": "11번가", "type": "마켓", "fee_rate": 11.0, "vat_included": False},
        {"name": "카페24", "type": "마켓", "fee_rate": 0.0, "vat_included": False},
        {"name": "네이버 검색광고", "type": "외부광고", "fee_rate": 0.0, "vat_included": True},
        {"name": "쿠팡 광고", "type": "외부광고", "fee_rate": 0.0, "vat_included": False},
        {"name": "지마켓/옥션 광고", "type": "외부광고", "fee_rate": 0.0, "vat_included": False},
        {"name": "메타 광고", "type": "외부광고", "fee_rate": 0.0, "vat_included": False},
        {"name": "구글 광고", "type": "외부광고", "fee_rate": 0.0, "vat_included": False},
    ])
    await _seed_if_empty(session, EventType, [
        {"name": "쿠폰 적용", "is_default": True},
        {"name": "목표 ROAS 변경", "is_default": True},
        {"name": "광고 예산 변경", "is_default": True},
        {"name": "판매가 수정", "is_default": True},
    ])
    await _seed_if_empty(session, CostCategory, [
        {"name": "인플루언서 비용", "type": "마케팅비"},
        {"name": "촬영비", "type": "마케팅비"},
        {"name": "모델비", "type": "마케팅비"},
        {"name": "물류비", "type": "마케팅비"},
        {"name": "행사진행비", "type": "마케팅비"},
        {"name": "체험단 비용", "type": "마케팅비"},
    ])
