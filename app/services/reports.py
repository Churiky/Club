from datetime import date, datetime, time

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.repositories.snapshots import SnapshotRepository


class ReportService:
    SCORE_FIELDS = {
        "daily": "daily_gain",
        "weekly": "seven_day_avg",
        "monthly": "monthly_gain",
    }

    def __init__(self, db: Session) -> None:
        self.db = db
        self.snapshots = SnapshotRepository(db)

    def current_report(self) -> list[dict]:
        return self.snapshots.fetch_current_report_rows()

    def leaderboard(self, period: str) -> list[dict]:
        if period not in self.SCORE_FIELDS:
            raise ValueError("period must be one of: daily, weekly, monthly")

        rows = self.current_report()
        score_field = self.SCORE_FIELDS[period]
        ranked = sorted(rows, key=lambda item: item.get(score_field) or 0, reverse=True)

        results = []
        for index, item in enumerate(ranked, start=1):
            results.append(
                {
                    "rank": index,
                    "member_id": item["member_id"],
                    "club_member_name": item["club_member_name"],
                    "period": period,
                    "score": item.get(score_field) or 0,
                    "fan_count": item.get("fan_count"),
                    "captured_at": item.get("captured_at"),
                }
            )
        return results

    def kpi_table(self, old_date: date) -> list[dict]:
        old_date_end = datetime.combine(old_date, time(23, 59, 59)).replace(microsecond=0)
        rows = self.db.execute(
            text(
                """
                SELECT
                    m.member_id,
                    m.club_member_name,
                    old_snap.captured_at AS date_old,
                    now_snap.captured_at AS date_now,
                    old_snap.fan_count AS fan_old,
                    now_snap.fan_count AS fan_now
                FROM app.members m
                LEFT JOIN LATERAL (
                    SELECT
                        fs.captured_at,
                        fs.fan_count
                    FROM app.fan_snapshots_new fs
                    WHERE fs.member_id = m.member_id
                    ORDER BY fs.captured_at DESC, fs.snapshot_new_id DESC
                    LIMIT 1
                ) AS now_snap ON TRUE
                LEFT JOIN LATERAL (
                    SELECT
                        fs.captured_at,
                        fs.fan_count
                    FROM app.fan_snapshots fs
                    WHERE fs.member_id = m.member_id
                      AND fs.captured_at <= :old_date_end
                    ORDER BY fs.captured_at DESC, fs.snapshot_id DESC
                    LIMIT 1
                ) AS old_snap ON TRUE
                WHERE m.is_active = TRUE
                  AND m.status_name = 'active'
                ORDER BY m.club_member_name
                """
            ),
            {"old_date_end": old_date_end},
        )

        result_rows = []
        for row in rows.mappings():
            date_old = self._coerce_datetime(row["date_old"])
            date_now = self._coerce_datetime(row["date_now"])
            fan_old = row["fan_old"]
            fan_now = row["fan_now"]

            fan_delta = None
            days_diff = None
            kpi_status = "Khong co du lieu"
            kpi_met = False
            fan_missing = None

            if date_old is not None and date_now is not None and fan_old is not None and fan_now is not None:
                fan_delta = fan_now - fan_old
                days_diff = (date_now.date() - date_old.date()).days

                if days_diff < 7:
                    kpi_status = "Chua du 7 ngay"
                else:
                    fan_missing = max(0, 10_000_000 - fan_delta)
                    if fan_delta >= 10_000_000:
                        kpi_status = "Dat KPI"
                        kpi_met = True
                        fan_missing = 0
                    else:
                        kpi_status = "Thieu KPI"

            result_rows.append(
                {
                    "member_id": row["member_id"],
                    "member_name": row["club_member_name"],
                    "uid": row["member_id"],
                    "date_old": date_old,
                    "date_now": date_now,
                    "fan_old": fan_old,
                    "fan_now": fan_now,
                    "fan_delta": fan_delta,
                    "days_diff": days_diff,
                    "kpi_status": kpi_status,
                    "kpi_met": kpi_met,
                    "fan_missing": fan_missing,
                }
            )

        return result_rows

    @staticmethod
    def _coerce_datetime(value):
        if value is None or isinstance(value, datetime):
            return value
        if isinstance(value, str):
            normalized = value.strip().replace("Z", "")
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%d.%m.%Y", "%Y-%m-%d"):
                try:
                    return datetime.strptime(normalized, fmt)
                except ValueError:
                    continue
        return value
