from fastapi import APIRouter, HTTPException

from app.api.deps import AppSettings, DbSession
from app.repositories.sync_runs import SyncRunRepository
from app.schemas.sync import HistoricalImportRequest, SyncRequest, SyncRunRead
from app.services.sync_service import SyncService

router = APIRouter(prefix="/api/sync", tags=["sync"])


@router.post("/run")
async def run_sync(payload: SyncRequest, db: DbSession, settings: AppSettings) -> dict:
    service = SyncService(db, settings)
    try:
        return await service.run_sync(
            requested_by=payload.requested_by,
            trigger_type="manual_command",
            source_type=payload.source_type,
            auto_create_missing_members=payload.auto_create_missing_members,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/run/{member_id}")
async def run_member_sync(member_id: int, payload: SyncRequest, db: DbSession, settings: AppSettings) -> dict:
    service = SyncService(db, settings)
    try:
        return await service.run_sync(
            requested_by=payload.requested_by,
            trigger_type="manual_command",
            source_type=payload.source_type,
            member_id=member_id,
            auto_create_missing_members=payload.auto_create_missing_members,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/import-old")
async def import_old_date(payload: HistoricalImportRequest, db: DbSession, settings: AppSettings) -> dict:
    service = SyncService(db, settings)
    try:
        return await service.import_old_date_from_web(
            requested_by=payload.requested_by,
            snapshot_date=payload.snapshot_date,
            source_type=payload.source_type,
            auto_create_missing_members=payload.auto_create_missing_members,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/runs", response_model=list[SyncRunRead])
def list_sync_runs(db: DbSession, limit: int = 100) -> list[SyncRunRead]:
    rows = SyncRunRepository(db).list_runs(limit=limit)
    return [SyncRunRead.model_validate(item) for item in rows]


@router.get("/runs/{sync_run_id}", response_model=SyncRunRead)
def get_sync_run(sync_run_id: int, db: DbSession) -> SyncRunRead:
    item = SyncRunRepository(db).get_run(sync_run_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Sync run not found.")
    return SyncRunRead.model_validate(item)
