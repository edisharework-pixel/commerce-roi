from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user
from app.models.ad import AdAnalysisLog
from app.services.ai_analyzer import AIAdAnalyzer

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/ads")
async def analyze_ads(
    product_id: int = Query(...),
    period_start: date = Query(...),
    period_end: date = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    analyzer = AIAdAnalyzer(db)
    return await analyzer.analyze_product_ads(product_id, period_start, period_end)


@router.get("/ads/history")
async def get_analysis_history(
    product_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    stmt = select(AdAnalysisLog).order_by(AdAnalysisLog.created_at.desc())
    if product_id:
        stmt = stmt.where(AdAnalysisLog.product_id == product_id)
    result = await db.execute(stmt)
    logs = result.scalars().all()
    return [{"id": l.id, "product_id": l.product_id, "period_start": str(l.period_start),
             "period_end": str(l.period_end), "analysis_result": l.analysis_result,
             "suggestions": l.suggestions, "created_at": str(l.created_at)} for l in logs]
