from datetime import date, datetime
from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class UploadHistory(Base):
    __tablename__ = "upload_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    platform_id: Mapped[int] = mapped_column(ForeignKey("platforms.id"))
    data_type: Mapped[str] = mapped_column(String(50))
    file_name: Mapped[str] = mapped_column(String(500))
    record_count: Mapped[int] = mapped_column(Integer)
    matched_count: Mapped[int] = mapped_column(Integer, default=0)
    unmatched_count: Mapped[int] = mapped_column(Integer, default=0)
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class MatchingLog(Base):
    __tablename__ = "matching_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    platform_product_name: Mapped[str] = mapped_column(String(500))
    matched_product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id"), nullable=True
    )
    method: Mapped[str] = mapped_column(String(20))
    confidence: Mapped[float] = mapped_column(Numeric(5, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
