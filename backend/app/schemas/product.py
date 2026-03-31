from decimal import Decimal

from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    sku: str
    base_cost: Decimal
    category: str


class ProductOut(BaseModel):
    id: int
    name: str
    sku: str
    base_cost: Decimal
    category: str
    model_config = {"from_attributes": True}


class PlatformProductOut(BaseModel):
    id: int
    product_id: int
    platform_id: int
    platform_product_id: str
    platform_product_name: str
    selling_price: Decimal | None
    platform_fee_rate: Decimal | None
    sale_status: str | None
    site: str | None
    matched_by: str
    model_config = {"from_attributes": True}


class UnmatchedProductOut(BaseModel):
    id: int
    platform_product_id: str
    platform_product_name: str
    platform_id: int
    matched_by: str
    model_config = {"from_attributes": True}
