from datetime import date, datetime
from pydantic import BaseModel


class EventTypeOut(BaseModel):
    id: int
    name: str
    is_default: bool
    model_config = {"from_attributes": True}


class EventTypeCreate(BaseModel):
    name: str


class ChangeEventCreate(BaseModel):
    event_type_id: int
    product_id: int | None = None
    platform_id: int | None = None
    description: str
    change_details: dict
    event_date: date


class ChangeEventOut(BaseModel):
    id: int
    event_type_id: int
    product_id: int | None
    platform_id: int | None
    description: str
    change_details: dict
    event_date: date
    created_at: datetime
    model_config = {"from_attributes": True}
