from datetime import datetime

from sqlalchemy import desc, select, text
from sqlalchemy.orm import Session

from app.models import MemberSyncLog, SyncRun


class SyncRunRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_run(
        self,
        *,
        trigger_type: str,
        source_type: str,
        requested_by: str | None,
        total_members: int,
        status_name: str = "running",
        raw_payload: str | None = None,
    ) -> SyncRun:
        started_at = datetime.utcnow().replace(microsecond=0)
        self.db.execute(
            text(
                """
                INSERT INTO app.sync_runs (
                    trigger_type,
                    source_type,
                    status_name,
                    started_at,
                    requested_by,
                    total_members,
                    success_count,
                    fail_count,
                    raw_payload
                )
                VALUES (
                    :trigger_type,
                    :source_type,
                    :status_name,
                    :started_at,
                    :requested_by,
                    :total_members,
                    0,
                    0,
                    :raw_payload
                )
                """
            ),
            {
                "trigger_type": trigger_type,
                "source_type": source_type,
                "status_name": status_name,
                "started_at": started_at,
                "requested_by": requested_by,
                "total_members": total_members,
                "raw_payload": raw_payload,
            },
        )
        stmt = (
            select(SyncRun)
            .where(
                SyncRun.trigger_type == trigger_type,
                SyncRun.source_type == source_type,
                SyncRun.status_name == status_name,
                SyncRun.started_at == started_at,
            )
            .order_by(desc(SyncRun.sync_run_id))
        )
        run = self.db.scalars(stmt).first()
        if run is None:
            raise RuntimeError("Failed to load sync run after insert.")
        return run

    def complete_run(
        self,
        run: SyncRun,
        *,
        status_name: str,
        success_count: int,
        fail_count: int,
        error_message: str | None = None,
    ) -> SyncRun:
        run.status_name = status_name
        run.success_count = success_count
        run.fail_count = fail_count
        run.error_message = error_message
        run.finished_at = datetime.utcnow()
        self.db.flush()
        return run

    def log_member(
        self,
        *,
        sync_run_id: int,
        member_id: int,
        status_name: str,
        fan_count: int | None,
        message: str | None,
    ) -> MemberSyncLog:
        created_at = datetime.utcnow().replace(microsecond=0)
        self.db.execute(
            text(
                """
                INSERT INTO app.member_sync_logs (
                    sync_run_id,
                    member_id,
                    status_name,
                    fan_count,
                    message,
                    created_at
                )
                VALUES (
                    :sync_run_id,
                    :member_id,
                    :status_name,
                    :fan_count,
                    :message,
                    :created_at
                )
                """
            ),
            {
                "sync_run_id": sync_run_id,
                "member_id": member_id,
                "status_name": status_name,
                "fan_count": fan_count,
                "message": message,
                "created_at": created_at,
            },
        )
        stmt = (
            select(MemberSyncLog)
            .where(
                MemberSyncLog.sync_run_id == sync_run_id,
                MemberSyncLog.member_id == member_id,
                MemberSyncLog.created_at == created_at,
            )
            .order_by(desc(MemberSyncLog.member_sync_log_id))
        )
        item = self.db.scalars(stmt).first()
        if item is None:
            raise RuntimeError("Failed to load member sync log after insert.")
        return item

    def list_runs(self, limit: int = 100) -> list[SyncRun]:
        stmt = select(SyncRun).order_by(desc(SyncRun.started_at)).limit(limit)
        return list(self.db.scalars(stmt))

    def get_run(self, sync_run_id: int) -> SyncRun | None:
        return self.db.get(SyncRun, sync_run_id)
