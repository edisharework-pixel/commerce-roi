from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class SalesSummary(Base):
    __tablename__ = "sales_summary"
    id: Mapped[int] = mapped_column(primary_key=True)
    platform_product_id: Mapped[int] = mapped_column(
        ForeignKey("platform_products.id")
    )
    option_id: Mapped[int | None] = mapped_column(
        ForeignKey("platform_product_options.id"), nullable=True
    )
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    gross_revenue: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    net_revenue: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    quantity: Mapped[int] = mapped_column(Integer)
    cancel_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2), nullable=True
    )
    cancel_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    refund_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2), nullable=True
    )
    refund_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    coupon_seller: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2), nullable=True
    )
    coupon_order: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2), nullable=True
    )
    visitors: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_views: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cart_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    conversion_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    upload_id: Mapped[int] = mapped_column(ForeignKey("upload_history.id"))


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    platform_product_id: Mapped[int] = mapped_column(
        ForeignKey("platform_products.id")
    )
    option_id: Mapped[int | None] = mapped_column(
        ForeignKey("platform_product_options.id"), nullable=True
    )
    order_date: Mapped[date] = mapped_column(Date)
    order_number: Mapped[str] = mapped_column(String(100), unique=True)
    quantity: Mapped[int] = mapped_column(Integer)
    sale_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    shipping_fee: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    platform_fee: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    cancelled_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    cancelled_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    refund_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    status: Mapped[str] = mapped_column(String(50))
    site: Mapped[str | None] = mapped_column(String(10), nullable=True)
    upload_id: Mapped[int] = mapped_column(ForeignKey("upload_history.id"))
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Settlement(Base):
    __tablename__ = "settlements"
    id: Mapped[int] = mapped_column(primary_key=True)
    platform_id: Mapped[int] = mapped_column(ForeignKey("platforms.id"))
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    expected_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    actual_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20))
