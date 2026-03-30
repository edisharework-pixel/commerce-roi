from decimal import Decimal
from sqlalchemy import Boolean, ForeignKey, JSON, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(500))
    sku: Mapped[str] = mapped_column(String(100), unique=True)
    base_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    category: Mapped[str] = mapped_column(String(200))
    platform_products: Mapped[list["PlatformProduct"]] = relationship(
        back_populates="product"
    )


class PlatformProduct(Base):
    __tablename__ = "platform_products"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    platform_id: Mapped[int] = mapped_column(ForeignKey("platforms.id"))
    platform_product_id: Mapped[str] = mapped_column(String(100))
    platform_product_name: Mapped[str] = mapped_column(String(500))
    seller_product_code: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
    selling_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    discount_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    platform_fee_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    shipping_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    shipping_fee: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    return_shipping_fee: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    exchange_shipping_fee: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    sale_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    site: Mapped[str | None] = mapped_column(String(10), nullable=True)
    master_product_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    matched_by: Mapped[str] = mapped_column(String(20))
    product: Mapped["Product"] = relationship(back_populates="platform_products")
    options: Mapped[list["PlatformProductOption"]] = relationship(
        back_populates="platform_product"
    )


class PlatformProductOption(Base):
    __tablename__ = "platform_product_options"
    __table_args__ = (
        UniqueConstraint(
            "platform_product_id", "option_id", name="uq_pp_option"
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    platform_product_id: Mapped[int] = mapped_column(
        ForeignKey("platform_products.id")
    )
    option_id: Mapped[str] = mapped_column(String(100))
    option_name: Mapped[str] = mapped_column(String(500))
    option_values: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    platform_product: Mapped["PlatformProduct"] = relationship(
        back_populates="options"
    )
