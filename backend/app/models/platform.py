from decimal import Decimal
from sqlalchemy import Boolean, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Platform(Base):
    __tablename__ = "platforms"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    type: Mapped[str] = mapped_column(String(50))
    fee_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    vat_included: Mapped[bool] = mapped_column(Boolean, default=False)
    site_identifier: Mapped[str | None] = mapped_column(String(10), nullable=True)
    seller_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
