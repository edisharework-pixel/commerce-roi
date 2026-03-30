from datetime import date
from sqlalchemy import Boolean, Date, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin


class EventType(Base):
    __tablename__ = "event_types"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )


class ChangeEvent(TimestampMixin, Base):
    __tablename__ = "change_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_type_id: Mapped[int] = mapped_column(ForeignKey("event_types.id"))
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id"), nullable=True
    )
    platform_id: Mapped[int | None] = mapped_column(
        ForeignKey("platforms.id"), nullable=True
    )
    description: Mapped[str] = mapped_column(Text)
    change_details: Mapped[dict] = mapped_column(JSON)
    event_date: Mapped[date] = mapped_column(Date)
