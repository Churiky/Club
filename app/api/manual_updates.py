from fastapi import APIRouter, HTTPException

from app.api.deps import DbSession
from app.repositories.snapshots import SnapshotRepository
from app.schemas.sync import ManualUpdateBulkRequest, ManualUpdateRead, ManualUpdateRequest
from app.services.manual_updates import ManualUpdateService

router = APIRouter(prefix="/api/manual-updates", tags=["manual-updates"])


@router.post("")
def create_manual_update(payload: ManualUpdateRequest, db: DbSession) -> dict:
    service = ManualUpdateService(db)
    try:
        return service.create_manual_update(payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/bulk")
def create_bulk_manual_updates(payload: ManualUpdateBulkRequest, db: DbSession) -> dict:
    service = ManualUpdateService(db)
    try:
        return service.create_bulk_manual_updates(payload.updates)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("", response_model=list[ManualUpdateRead])
def list_manual_updates(db: DbSession, limit: int = 100) -> list[ManualUpdateRead]:
    rows = SnapshotRepository(db).list_manual_updates(limit=limit)
    return [
        ManualUpdateRead(
            manual_update_id=item.manual_update_id,
            member_id=item.member_id,
            snapshot_id=item.snapshot_id,
            updated_by=item.updated_by,
            fan_count=item.fan_count,
            note=item.note,
            created_at=item.created_at,
        )
        for item in rows
    ]
