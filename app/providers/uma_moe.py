import re
from datetime import date, datetime

import httpx

from app.config import Settings
from app.providers.base import FanDataProvider, ProviderMemberSnapshot


class UmaMoeProvider(FanDataProvider):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def fetch_club_members(self, club_id: str) -> list[ProviderMemberSnapshot]:
        text_url = f"{self.settings.uma_moe_text_proxy_url}/circles/{club_id}"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(text_url)
            response.raise_for_status()
        return self._parse_member_sections(response.text, club_id)

    def _parse_member_sections(self, content: str, club_id: str) -> list[ProviderMemberSnapshot]:
        marker = "## Members"
        if marker not in content:
            raise ValueError("Could not find members section in uma.moe response.")

        body = content.split(marker, 1)[1]
        body = body.split("cookie Cookie Settings", 1)[0]

        pattern = re.compile(
            r"#(?P<rank>\d+)\s+"
            r"(?P<name>.+?)\s+"
            r"(?P<role>Leader|Officer|Member(?: Left)?)\s+"
            r"Total Fans (?P<fan>[\d,]+)\s+"
            r"Monthly Gain\+(?P<monthly>[\d,]+)"
            r"(?:.*?7 Day Avg\+(?P<weekly>[\d,]+))?"
            r"(?:.*?Daily Gain\+(?P<daily>[\d,]+))?"
            r"\s+Last Updated (?P<date>\d{2}\.\d{2}\.\d{4})",
            re.DOTALL,
        )

        items: list[ProviderMemberSnapshot] = []
        for match in pattern.finditer(body):
            role_text = match.group("role").strip().lower()
            status_name = "left" if "left" in role_text else "active"
            role_name = "member"
            if role_text.startswith("leader"):
                role_name = "leader"
            elif role_text.startswith("officer"):
                role_name = "officer"

            date_value = datetime.strptime(match.group("date"), "%d.%m.%Y")
            items.append(
                ProviderMemberSnapshot(
                    member_name=self._clean_whitespace(match.group("name")),
                    role_name=role_name,
                    status_name=status_name,
                    fan_count=self._parse_int(match.group("fan")),
                    monthly_gain=self._parse_int(match.group("monthly")),
                    daily_gain=self._parse_int(match.group("daily")),
                    seven_day_avg=self._parse_int(match.group("weekly")),
                    captured_at=date_value,
                    source_ref=f"{self.settings.uma_moe_base_url}/circles/{club_id}",
                )
            )

        if not items:
            raise ValueError("Could not parse member data from uma.moe page.")

        return items

    async def fetch_club_members_by_date(self, club_id: str, snapshot_date: date) -> list[ProviderMemberSnapshot]:
        api_url = (
            f"{self.settings.uma_moe_base_url}/api/v4/circles"
            f"?circle_id={club_id}&year={snapshot_date.year}&month={snapshot_date.month}"
        )
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                api_url,
                headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
            )
            response.raise_for_status()
            payload = response.json()
        return self._parse_historical_members(payload, club_id, snapshot_date)

    def _parse_historical_members(
        self,
        payload: dict,
        club_id: str,
        snapshot_date: date,
    ) -> list[ProviderMemberSnapshot]:
        members = payload.get("members")
        if not isinstance(members, list):
            raise ValueError("Could not find historical members data in uma.moe response.")

        day_index = snapshot_date.day - 1
        captured_at = datetime.combine(snapshot_date, datetime.min.time())
        source_ref = (
            f"{self.settings.uma_moe_base_url}/circles/{club_id}"
            f"?year={snapshot_date.year}&month={snapshot_date.month}"
        )

        items: list[ProviderMemberSnapshot] = []
        for member in members:
            trainer_name = self._clean_whitespace(str(member.get("trainer_name") or ""))
            daily_fans = member.get("daily_fans") or []
            if not trainer_name or not isinstance(daily_fans, list) or day_index >= len(daily_fans):
                continue

            fan_count = daily_fans[day_index]
            if not isinstance(fan_count, int) or fan_count <= 0:
                continue

            daily_gain = None
            if day_index > 0:
                previous_fan = daily_fans[day_index - 1]
                if isinstance(previous_fan, int) and previous_fan > 0:
                    daily_gain = fan_count - previous_fan

            seven_day_avg = None
            window_start = max(0, day_index - 6)
            if day_index > 0:
                valid_window = [
                    value
                    for value in daily_fans[window_start : day_index + 1]
                    if isinstance(value, int) and value > 0
                ]
                if len(valid_window) >= 2:
                    seven_day_avg = int((valid_window[-1] - valid_window[0]) / (len(valid_window) - 1))

            monthly_gain = None
            month_start_value = next(
                (value for value in daily_fans if isinstance(value, int) and value > 0),
                None,
            )
            if month_start_value is not None:
                monthly_gain = fan_count - month_start_value

            items.append(
                ProviderMemberSnapshot(
                    member_name=trainer_name,
                    role_name="member",
                    status_name="active",
                    fan_count=fan_count,
                    monthly_gain=monthly_gain,
                    daily_gain=daily_gain,
                    seven_day_avg=seven_day_avg,
                    captured_at=captured_at,
                    source_ref=source_ref,
                )
            )

        if not items:
            raise ValueError(f"Could not parse historical fan data for {snapshot_date.isoformat()} from uma.moe.")

        return items

    @staticmethod
    def _parse_int(value: str | None) -> int | None:
        if value is None:
            return None
        return int(value.replace(",", "").strip())

    @staticmethod
    def _clean_whitespace(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()
