from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel


class MemberCreate(BaseModel):
    club_member_name: str
    external_name: str | None = None
    role_name: str = "member"
    status_name: str = "active"
    is_active: bool = True
    notes: str | None = None


class MemberUpdate(BaseModel):
    external_name: str | None = None
    role_name: str | None = None
    status_name: str | None = None
    is_active: bool | None = None
    notes: str | None = None


class MemberRead(ORMModel):
    member_id: int
    club_member_name: str
    external_name: str | None
    role_name: str
    status_name: str
    is_active: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime


class MemberHistoryRow(BaseModel):
    snapshot_id: int
    fan_count: int
    monthly_gain: int | None = None
    daily_gain: int | None = None
    seven_day_avg: int | None = None
    captured_at: datetime
    source_type: str
    source_ref: str | None = None
    note: str | None = None
