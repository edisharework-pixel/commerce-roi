from decimal import Decimal

from pydantic import BaseModel


class PlatformCreate(BaseModel):
    name: str
    type: str
    fee_rate: Decimal
    vat_included: bool = False
    site_identifier: str | None = None
    seller_id: str | None = None


class PlatformOut(BaseModel):
    id: int
    name: str
    type: str
    fee_rate: Decimal
    vat_included: bool
    site_identifier: str | None
    seller_id: str | None
    model_config = {"from_attributes": True}
