from datetime import date
from decimal import Decimal
from sqlalchemy import Date, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin


class AdData(Base):
    __tablename__ = "ad_data"
    id: Mapped[int] = mapped_column(primary_key=True)
    platform_id: Mapped[int] = mapped_column(ForeignKey("platforms.id"))
    platform_product_id: Mapped[int | None] = mapped_column(
        ForeignKey("platform_products.id"), nullable=True
    )
    option_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    campaign_name: Mapped[str] = mapped_column(String(500))
    ad_group: Mapped[str | None] = mapped_column(String(500), nullable=True)
    keyword: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ad_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    exposure_area: Mapped[str | None] = mapped_column(String(100), nullable=True)
    device: Mapped[str | None] = mapped_column(String(20), nullable=True)
    spend: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    impressions: Mapped[int] = mapped_column(Integer)
    clicks: Mapped[int] = mapped_column(Integer)
    direct_conversions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    indirect_conversions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    direct_revenue: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2), nullable=True
    )
    indirect_revenue: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2), nullable=True
    )
    attribution_window: Mapped[str | None] = mapped_column(String(10), nullable=True)
    avg_rank: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    site: Mapped[str | None] = mapped_column(String(10), nullable=True)
    ad_date: Mapped[date] = mapped_column(Date)
    match_status: Mapped[str] = mapped_column(String(20), default="pending")
    extended_metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class AdCampaignProductMapping(TimestampMixin, Base):
    __tablename__ = "ad_campaign_product_mapping"
    id: Mapped[int] = mapped_column(primary_key=True)
    platform_id: Mapped[int] = mapped_column(ForeignKey("platforms.id"))
    campaign_name: Mapped[str] = mapped_column(String(500))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    allocation_method: Mapped[str] = mapped_column(String(30))


class AdAnalysisLog(TimestampMixin, Base):
    __tablename__ = "ad_analysis_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    analysis_result: Mapped[dict] = mapped_column(JSON)
    suggestions: Mapped[str] = mapped_column(Text)
