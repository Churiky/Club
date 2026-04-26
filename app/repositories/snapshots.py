from datetime import datetime

from sqlalchemy import desc, select, text
from sqlalchemy.orm import Session

from app.models import FanSnapshot, FanSnapshotNew, ManualUpdate


class SnapshotRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_snapshot(
        self,
        *,
        member_id: int,
        sync_run_id: int | None,
        fan_count: int,
        monthly_gain: int | None,
        daily_gain: int | None,
        seven_day_avg: int | None,
        captured_at: datetime,
        source_type: str,
        source_ref: str | None,
        note: str | None,
    ) -> FanSnapshot:
        created_at = datetime.utcnow().replace(microsecond=0)
        captured_at = captured_at.replace(microsecond=0)
        self.db.execute(
            text(
                """
                INSERT INTO app.fan_snapshots (
                    member_id,
                    sync_run_id,
                    fan_count,
                    monthly_gain,
                    daily_gain,
                    seven_day_avg,
                    captured_at,
                    source_type,
                    source_ref,
                    note,
                    created_at
                )
                VALUES (
                    :member_id,
                    :sync_run_id,
                    :fan_count,
                    :monthly_gain,
                    :daily_gain,
                    :seven_day_avg,
                    :captured_at,
                    :source_type,
                    :source_ref,
                    :note,
                    :created_at
                )
                """
            ),
            {
                "member_id": member_id,
                "sync_run_id": sync_run_id,
                "fan_count": fan_count,
                "monthly_gain": monthly_gain,
                "daily_gain": daily_gain,
                "seven_day_avg": seven_day_avg,
                "captured_at": captured_at,
                "source_type": source_type,
                "source_ref": source_ref,
                "note": note,
                "created_at": created_at,
            },
        )
        stmt = (
            select(FanSnapshot)
            .where(
                FanSnapshot.member_id == member_id,
                FanSnapshot.captured_at == captured_at,
                FanSnapshot.created_at == created_at,
            )
            .order_by(desc(FanSnapshot.snapshot_id))
        )
        snapshot = self.db.scalars(stmt).first()
        if snapshot is None:
            raise RuntimeError("Failed to load snapshot after insert.")
        return snapshot

    def create_manual_update(
        self,
        *,
        member_id: int,
        snapshot_id: int | None,
        updated_by: str,
        fan_count: int,
        note: str | None,
    ) -> ManualUpdate:
        created_at = datetime.utcnow().replace(microsecond=0)
        self.db.execute(
            text(
                """
                INSERT INTO app.manual_updates (
                    member_id,
                    snapshot_id,
                    updated_by,
                    fan_count,
                    note,
                    created_at
                )
                VALUES (
                    :member_id,
                    :snapshot_id,
                    :updated_by,
                    :fan_count,
                    :note,
                    :created_at
                )
                """
            ),
            {
                "member_id": member_id,
                "snapshot_id": snapshot_id,
                "updated_by": updated_by,
                "fan_count": fan_count,
                "note": note,
                "created_at": created_at,
            },
        )
        stmt = (
            select(ManualUpdate)
            .where(
                ManualUpdate.member_id == member_id,
                ManualUpdate.created_at == created_at,
                ManualUpdate.updated_by == updated_by,
            )
            .order_by(desc(ManualUpdate.manual_update_id))
        )
        manual = self.db.scalars(stmt).first()
        if manual is None:
            raise RuntimeError("Failed to load manual update after insert.")
        return manual

    def replace_latest_snapshots_new(
        self,
        *,
        sync_run_id: int | None,
        snapshots: list[dict],
    ) -> None:
        self.db.execute(text("DELETE FROM app.fan_snapshots_new"))
        for item in snapshots:
            created_at = datetime.utcnow().replace(microsecond=0)
            captured_at = item["captured_at"].replace(microsecond=0)
            self.db.execute(
                text(
                    """
                    INSERT INTO app.fan_snapshots_new (
                        member_id,
                        sync_run_id,
                        fan_count,
                        monthly_gain,
                        daily_gain,
                        seven_day_avg,
                        captured_at,
                        source_type,
                        source_ref,
                        note,
                        created_at
                    )
                    VALUES (
                        :member_id,
                        :sync_run_id,
                        :fan_count,
                        :monthly_gain,
                        :daily_gain,
                        :seven_day_avg,
                        :captured_at,
                        :source_type,
                        :source_ref,
                        :note,
                        :created_at
                    )
                    """
                ),
                {
                    "member_id": item["member_id"],
                    "sync_run_id": sync_run_id,
                    "fan_count": item["fan_count"],
                    "monthly_gain": item.get("monthly_gain"),
                    "daily_gain": item.get("daily_gain"),
                    "seven_day_avg": item.get("seven_day_avg"),
                    "captured_at": captured_at,
                    "source_type": item["source_type"],
                    "source_ref": item.get("source_ref"),
                    "note": item.get("note"),
                    "created_at": created_at,
                },
            )

    def replace_old_snapshots_for_date(
        self,
        *,
        sync_run_id: int | None,
        snapshots: list[dict],
    ) -> None:
        for item in snapshots:
            captured_at = item["captured_at"].replace(microsecond=0)
            self.db.execute(
                text(
                    """
                    DELETE FROM app.fan_snapshots
                    WHERE member_id = :member_id
                      AND captured_at = :captured_at
                      AND source_type = :source_type
                    """
                ),
                {
                    "member_id": item["member_id"],
                    "captured_at": captured_at,
                    "source_type": item["source_type"],
                },
            )
            self.create_snapshot(
                member_id=item["member_id"],
                sync_run_id=sync_run_id,
                fan_count=item["fan_count"],
                monthly_gain=item.get("monthly_gain"),
                daily_gain=item.get("daily_gain"),
                seven_day_avg=item.get("seven_day_avg"),
                captured_at=captured_at,
                source_type=item["source_type"],
                source_ref=item.get("source_ref"),
                note=item.get("note"),
            )

    def list_snapshots_new(self) -> list[FanSnapshotNew]:
        stmt = select(FanSnapshotNew).order_by(desc(FanSnapshotNew.captured_at), desc(FanSnapshotNew.snapshot_new_id))
        return list(self.db.scalars(stmt))

    def list_history(self, member_id: int) -> list[FanSnapshot]:
        stmt = (
            select(FanSnapshot)
            .where(FanSnapshot.member_id == member_id)
            .order_by(desc(FanSnapshot.captured_at), desc(FanSnapshot.snapshot_id))
        )
        return list(self.db.scalars(stmt))

    def list_manual_updates(self, limit: int = 100) -> list[ManualUpdate]:
        stmt = select(ManualUpdate).order_by(desc(ManualUpdate.created_at)).limit(limit)
        return list(self.db.scalars(stmt))

    def fetch_current_report_rows(self) -> list[dict]:
        result = self.db.execute(
            text(
                """
                SELECT
                    m.member_id,
                    m.club_member_name,
                    m.role_name,
                    m.status_name,
                    m.is_active,
                    COALESCE(now_snap.fan_count, old_view.fan_count) AS fan_count,
                    COALESCE(now_snap.monthly_gain, old_view.monthly_gain) AS monthly_gain,
                    COALESCE(now_snap.daily_gain, old_view.daily_gain) AS daily_gain,
                    COALESCE(now_snap.seven_day_avg, old_view.seven_day_avg) AS seven_day_avg,
                    COALESCE(now_snap.captured_at, old_view.captured_at) AS captured_at,
                    COALESCE(now_snap.source_type, old_view.source_type) AS source_type
                FROM app.members m
                LEFT JOIN app.v_member_current_kpi old_view
                    ON old_view.member_id = m.member_id
                OUTER APPLY (
                    SELECT TOP 1
                        fs.fan_count,
                        fs.monthly_gain,
                        fs.daily_gain,
                        fs.seven_day_avg,
                        fs.captured_at,
                        fs.source_type
                    FROM app.fan_snapshots_new fs
                    WHERE fs.member_id = m.member_id
                    ORDER BY fs.captured_at DESC, fs.snapshot_new_id DESC
                ) now_snap
                WHERE m.is_active = 1
                  AND m.status_name = 'active'
                ORDER BY m.club_member_name
                """
            )
        )
        return [dict(row._mapping) for row in result]
