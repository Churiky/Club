from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class SyncRequest(BaseModel):
    requested_by: str = "admin"
    source_type: str = "uma_moe"
    auto_create_missing_members: bool = True


class HistoricalImportRequest(BaseModel):
    requested_by: str = "admin"
    source_type: str = "uma_moe"
    snapshot_date: date
    auto_create_missing_members: bool = True


class ManualUpdateRequest(BaseModel):
    member_id: int
    fan_count: int = Field(ge=0)
    monthly_gain: int | None = Field(default=None, ge=0)
    daily_gain: int | None = Field(default=None, ge=0)
    seven_day_avg: int | None = Field(default=None, ge=0)
    captured_at: datetime | None = None
    updated_by: str
    note: str | None = None


class ManualUpdateBulkRequest(BaseModel):
    updates: list[ManualUpdateRequest]


class SyncRunRead(ORMModel):
    sync_run_id: int
    trigger_type: str
    source_type: str
    status_name: str
    started_at: datetime
    finished_at: datetime | None
    requested_by: str | None
    total_members: int
    success_count: int
    fail_count: int
    error_message: str | None


class ManualUpdateRead(BaseModel):
    manual_update_id: int
    member_id: int
    snapshot_id: int | None = None
    updated_by: str
    fan_count: int
    note: str | None = None
    created_at: datetime
