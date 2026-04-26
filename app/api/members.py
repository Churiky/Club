from fastapi import APIRouter, HTTPException

from app.api.deps import AppSettings, DbSession
from app.repositories.members import MemberRepository
from app.repositories.snapshots import SnapshotRepository
from app.schemas.members import MemberCreate, MemberHistoryRow, MemberRead, MemberUpdate
from app.services.sync_service import SyncService

router = APIRouter(prefix="/api/members", tags=["members"])


@router.get("", response_model=list[MemberRead])
def list_members(db: DbSession) -> list[MemberRead]:
    repo = MemberRepository(db)
    return [MemberRead.model_validate(item) for item in repo.list_members()]


@router.post("/import-from-web")
async def import_members_from_web(db: DbSession, settings: AppSettings, requested_by: str = "admin") -> dict:
    service = SyncService(db, settings)
    try:
        return await service.import_members_from_web(requested_by=requested_by)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/{member_id}", response_model=MemberRead)
def get_member(member_id: int, db: DbSession) -> MemberRead:
    repo = MemberRepository(db)
    member = repo.get_by_id(member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found.")
    return MemberRead.model_validate(member)


@router.post("", response_model=MemberRead)
def create_member(payload: MemberCreate, db: DbSession) -> MemberRead:
    repo = MemberRepository(db)
    member = repo.create_member(payload.model_dump())
    db.commit()
    db.refresh(member)
    return MemberRead.model_validate(member)


@router.put("/{member_id}", response_model=MemberRead)
def update_member(member_id: int, payload: MemberUpdate, db: DbSession) -> MemberRead:
    repo = MemberRepository(db)
    member = repo.get_by_id(member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found.")

    values = {key: value for key, value in payload.model_dump().items() if value is not None}
    updated = repo.update_member(member, values)
    db.commit()
    return MemberRead.model_validate(updated)


@router.get("/{member_id}/history", response_model=list[MemberHistoryRow])
def member_history(member_id: int, db: DbSession) -> list[MemberHistoryRow]:
    snapshots = SnapshotRepository(db).list_history(member_id)
    return [
        MemberHistoryRow(
            snapshot_id=item.snapshot_id,
            fan_count=item.fan_count,
            monthly_gain=item.monthly_gain,
            daily_gain=item.daily_gain,
            seven_day_avg=item.seven_day_avg,
            captured_at=item.captured_at,
            source_type=item.source_type,
            source_ref=item.source_ref,
            note=item.note,
        )
        for item in snapshots
    ]

