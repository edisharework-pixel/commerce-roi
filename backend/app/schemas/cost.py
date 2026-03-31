from datetime import date
from decimal import Decimal
from pydantic import BaseModel


class CostCategoryOut(BaseModel):
    id: int
    name: str
    type: str
    model_config = {"from_attributes": True}


class CostCategoryCreate(BaseModel):
    name: str
    type: str


class VariableCostCreate(BaseModel):
    product_id: int
    category_id: int
    amount: Decimal
    period_start: date
    period_end: date


class VariableCostOut(BaseModel):
    id: int
    product_id: int
    category_id: int
    amount: Decimal
    period_start: date
    period_end: date
    model_config = {"from_attributes": True}


class CampaignCreate(BaseModel):
    name: str
    start_date: date
    end_date: date
    allocation_method: str
    product_ids: list[int] = []


class CampaignOut(BaseModel):
    id: int
    name: str
    start_date: date
    end_date: date
    allocation_method: str
    model_config = {"from_attributes": True}


class MarketingCostCreate(BaseModel):
    campaign_id: int | None = None
    category_id: int
    product_id: int | None = None
    amount: Decimal
    cost_date: date


class MarketingCostOut(BaseModel):
    id: int
    campaign_id: int | None
    category_id: int
    product_id: int | None
    amount: Decimal
    cost_date: date
    model_config = {"from_attributes": True}
