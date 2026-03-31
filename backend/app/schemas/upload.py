from datetime import date, datetime
from pydantic import BaseModel


class UploadResponse(BaseModel):
    upload_id: int
    record_count: int
    matched_count: int
    unmatched_count: int


class UploadHistoryOut(BaseModel):
    id: int
    platform_id: int
    data_type: str
    file_name: str
    record_count: int
    matched_count: int
    unmatched_count: int
    period_start: date
    period_end: date
    uploaded_at: datetime
    model_config = {"from_attributes": True}
