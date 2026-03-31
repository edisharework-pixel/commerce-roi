from datetime import date
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user
from app.models.upload import UploadHistory
from app.schemas.upload import UploadHistoryOut, UploadResponse
from app.services.upload_service import UploadService

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    platform_id: int = Form(...),
    data_type: str = Form(...),
    period_start: date = Form(...),
    period_end: date = Form(...),
    password: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    file_ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else "csv"
    file_type = "xlsx" if file_ext in ("xlsx", "xls") else "csv"
    service = UploadService(db)
    try:
        result = await service.process_upload(
            file=file.file,
            file_type=file_type,
            platform_id=platform_id,
            data_type=data_type,
            period_start=period_start,
            period_end=period_end,
            file_name=file.filename or "unknown",
            password=password,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return UploadResponse(
        upload_id=result.upload_id,
        record_count=result.record_count,
        matched_count=result.matched_count,
        unmatched_count=result.unmatched_count,
    )


@router.get("/history", response_model=list[UploadHistoryOut])
async def list_upload_history(
    platform_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    stmt = select(UploadHistory).order_by(UploadHistory.uploaded_at.desc())
    if platform_id:
        stmt = stmt.where(UploadHistory.platform_id == platform_id)
    result = await db.execute(stmt)
    return result.scalars().all()
