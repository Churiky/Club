from datetime import datetime

from sqlalchemy.orm import Session

from app.repositories.members import MemberRepository
from app.repositories.snapshots import SnapshotRepository
from app.repositories.sync_runs import SyncRunRepository
from app.schemas.sync import ManualUpdateRequest


class ManualUpdateService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.members = MemberRepository(db)
        self.snapshots = SnapshotRepository(db)
        self.sync_runs = SyncRunRepository(db)

    def create_manual_update(self, payload: ManualUpdateRequest) -> dict:
        member = self.members.get_by_id(payload.member_id)
        if member is None:
            raise ValueError(f"Member {payload.member_id} not found.")

        sync_run = self.sync_runs.create_run(
            trigger_type="manual_admin",
            source_type="admin_manual",
            requested_by=payload.updated_by,
            total_members=1,
        )

        captured_at = (payload.captured_at or datetime.utcnow()).replace(microsecond=0)
        snapshot = self.snapshots.create_snapshot(
            member_id=member.member_id,
            sync_run_id=sync_run.sync_run_id,
            fan_count=payload.fan_count,
            monthly_gain=payload.monthly_gain,
            daily_gain=payload.daily_gain,
            seven_day_avg=payload.seven_day_avg,
            captured_at=captured_at,
            source_type="admin_manual",
            source_ref="admin",
            note=payload.note,
        )

        manual = self.snapshots.create_manual_update(
            member_id=member.member_id,
            snapshot_id=snapshot.snapshot_id,
            updated_by=payload.updated_by,
            fan_count=payload.fan_count,
            note=payload.note,
        )

        self.sync_runs.log_member(
            sync_run_id=sync_run.sync_run_id,
            member_id=member.member_id,
            status_name="success",
            fan_count=payload.fan_count,
            message="Manual update saved successfully.",
        )

        self.sync_runs.complete_run(
            sync_run,
            status_name="success",
            success_count=1,
            fail_count=0,
        )
        self.db.commit()

        return {
            "sync_run_id": sync_run.sync_run_id,
            "snapshot_id": snapshot.snapshot_id,
            "manual_update_id": manual.manual_update_id,
            "member_id": member.member_id,
        }

    def create_bulk_manual_updates(self, updates: list[ManualUpdateRequest]) -> dict:
        results = []
        for item in updates:
            results.append(self.create_manual_update(item))
        return {"count": len(results), "items": results}
