from datetime import datetime

from pydantic import BaseModel


class CurrentMemberReport(BaseModel):
    member_id: int
    club_member_name: str
    role_name: str
    status_name: str
    is_active: bool
    fan_count: int | None = None
    monthly_gain: int | None = None
    daily_gain: int | None = None
    seven_day_avg: int | None = None
    captured_at: datetime | None = None
    source_type: str | None = None


class LeaderboardEntry(BaseModel):
    rank: int
    member_id: int
    club_member_name: str
    period: str
    score: int
    fan_count: int | None = None
    captured_at: datetime | None = None


class KpiTableRow(BaseModel):
    member_id: int
    member_name: str
    uid: int
    date_old: datetime | None = None
    date_now: datetime | None = None
    fan_old: int | None = None
    fan_now: int | None = None
    fan_delta: int | None = None
    days_diff: int | None = None
    kpi_status: str
    kpi_met: bool
    fan_missing: int | None = None
