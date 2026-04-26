from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class ProviderMemberSnapshot:
    member_name: str
    role_name: str
    status_name: str
    fan_count: int
    monthly_gain: int | None
    daily_gain: int | None
    seven_day_avg: int | None
    captured_at: datetime
    source_ref: str


class FanDataProvider:
    async def fetch_club_members(self, club_id: str) -> list[ProviderMemberSnapshot]:
        raise NotImplementedError

    async def fetch_club_members_by_date(self, club_id: str, snapshot_date: date) -> list[ProviderMemberSnapshot]:
        raise NotImplementedError
