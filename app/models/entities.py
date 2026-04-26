from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, NVARCHAR, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Member(Base):
    __tablename__ = "members"
    __table_args__ = {"schema": "app"}

    member_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    club_member_name: Mapped[str] = mapped_column(NVARCHAR(100), unique=True, nullable=False)
    external_name: Mapped[str | None] = mapped_column(NVARCHAR(100))
    role_name: Mapped[str] = mapped_column(NVARCHAR(20), nullable=False)
    status_name: Mapped[str] = mapped_column(NVARCHAR(20), nullable=False)
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
    notes: Mapped[str | None] = mapped_column(NVARCHAR(500))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=text("SYSUTCDATETIME()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=text("SYSUTCDATETIME()")
    )

    snapshots: Mapped[list["FanSnapshot"]] = relationship(back_populates="member")


class SyncRun(Base):
    __tablename__ = "sync_runs"
    __table_args__ = {"schema": "app"}

    sync_run_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    trigger_type: Mapped[str] = mapped_column(NVARCHAR(30), nullable=False)
    source_type: Mapped[str] = mapped_column(NVARCHAR(30), nullable=False)
    status_name: Mapped[str] = mapped_column(NVARCHAR(20), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=False))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
    requested_by: Mapped[str | None] = mapped_column(NVARCHAR(100))
    total_members: Mapped[int] = mapped_column(Integer, nullable=False)
    success_count: Mapped[int] = mapped_column(Integer, nullable=False)
    fail_count: Mapped[int] = mapped_column(Integer, nullable=False)
    error_message: Mapped[str | None] = mapped_column(NVARCHAR(2000))
    raw_payload: Mapped[str | None] = mapped_column(NVARCHAR(4000))

    snapshots: Mapped[list["FanSnapshot"]] = relationship(back_populates="sync_run")


class FanSnapshot(Base):
    __tablename__ = "fan_snapshots"
    __table_args__ = {"schema": "app"}

    snapshot_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("app.members.member_id"), nullable=False)
    sync_run_id: Mapped[int | None] = mapped_column(ForeignKey("app.sync_runs.sync_run_id"))
    fan_count: Mapped[int] = mapped_column(BigInteger, nullable=False)
    monthly_gain: Mapped[int | None] = mapped_column(BigInteger)
    daily_gain: Mapped[int | None] = mapped_column(BigInteger)
    seven_day_avg: Mapped[int | None] = mapped_column(BigInteger)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    source_type: Mapped[str] = mapped_column(NVARCHAR(30), nullable=False)
    source_ref: Mapped[str | None] = mapped_column(NVARCHAR(255))
    note: Mapped[str | None] = mapped_column(NVARCHAR(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False))

    member: Mapped["Member"] = relationship(back_populates="snapshots")
    sync_run: Mapped["SyncRun"] = relationship(back_populates="snapshots")


class FanSnapshotNew(Base):
    __tablename__ = "fan_snapshots_new"
    __table_args__ = {"schema": "app"}

    snapshot_new_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("app.members.member_id"), nullable=False)
    sync_run_id: Mapped[int | None] = mapped_column(ForeignKey("app.sync_runs.sync_run_id"))
    fan_count: Mapped[int] = mapped_column(BigInteger, nullable=False)
    monthly_gain: Mapped[int | None] = mapped_column(BigInteger)
    daily_gain: Mapped[int | None] = mapped_column(BigInteger)
    seven_day_avg: Mapped[int | None] = mapped_column(BigInteger)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    source_type: Mapped[str] = mapped_column(NVARCHAR(30), nullable=False)
    source_ref: Mapped[str | None] = mapped_column(NVARCHAR(255))
    note: Mapped[str | None] = mapped_column(NVARCHAR(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False))


class ManualUpdate(Base):
    __tablename__ = "manual_updates"
    __table_args__ = {"schema": "app"}

    manual_update_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("app.members.member_id"), nullable=False)
    snapshot_id: Mapped[int | None] = mapped_column(ForeignKey("app.fan_snapshots.snapshot_id"))
    updated_by: Mapped[str] = mapped_column(NVARCHAR(100), nullable=False)
    fan_count: Mapped[int] = mapped_column(BigInteger, nullable=False)
    note: Mapped[str | None] = mapped_column(NVARCHAR(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False))


class MemberSyncLog(Base):
    __tablename__ = "member_sync_logs"
    __table_args__ = {"schema": "app"}

    member_sync_log_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    sync_run_id: Mapped[int] = mapped_column(ForeignKey("app.sync_runs.sync_run_id"), nullable=False)
    member_id: Mapped[int] = mapped_column(ForeignKey("app.members.member_id"), nullable=False)
    status_name: Mapped[str] = mapped_column(NVARCHAR(20), nullable=False)
    fan_count: Mapped[int | None] = mapped_column(BigInteger)
    message: Mapped[str | None] = mapped_column(NVARCHAR(1000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False))
