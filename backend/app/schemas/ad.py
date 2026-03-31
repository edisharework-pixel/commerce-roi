from datetime import date
from decimal import Decimal
from pydantic import BaseModel


class AdDataOut(BaseModel):
    id: int
    platform_id: int
    platform_product_id: int | None
    campaign_name: str
    ad_type: str | None
    spend: Decimal
    impressions: int
    clicks: int
    direct_conversions: int | None
    indirect_conversions: int | None
    ad_date: date
    match_status: str
    model_config = {"from_attributes": True}


class AdCampaignMappingCreate(BaseModel):
    platform_id: int
    campaign_name: str
    product_id: int
    allocation_method: str = "single"


class AdCampaignMappingOut(BaseModel):
    id: int
    platform_id: int
    campaign_name: str
    product_id: int
    allocation_method: str
    model_config = {"from_attributes": True}
