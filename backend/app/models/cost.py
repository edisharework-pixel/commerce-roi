from datetime import date
from decimal import Decimal
from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class CostCategory(Base):
    __tablename__ = "cost_categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(50))


class VariableCost(Base):
    __tablename__ = "variable_costs"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    category_id: Mapped[int] = mapped_column(ForeignKey("cost_categories.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)


class Campaign(Base):
    __tablename__ = "campaigns"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(300))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    allocation_method: Mapped[str] = mapped_column(String(30))


class CampaignProduct(Base):
    __tablename__ = "campaign_products"
    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))


class MarketingCost(Base):
    __tablename__ = "marketing_costs"
    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaigns.id"), nullable=True
    )
    category_id: Mapped[int] = mapped_column(ForeignKey("cost_categories.id"))
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id"), nullable=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    cost_date: Mapped[date] = mapped_column(Date)
