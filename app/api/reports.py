from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import DbSession
from app.schemas.reports import CurrentMemberReport, KpiTableRow, LeaderboardEntry
from app.services.reports import ReportService

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/current", response_model=list[CurrentMemberReport])
def current_report(db: DbSession) -> list[CurrentMemberReport]:
    rows = ReportService(db).current_report()
    return [CurrentMemberReport(**item) for item in rows]


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
def leaderboard(
    db: DbSession,
    period: str = Query(default="monthly"),
) -> list[LeaderboardEntry]:
    try:
        rows = ReportService(db).leaderboard(period)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [LeaderboardEntry(**item) for item in rows]


@router.get("/kpi-table", response_model=list[KpiTableRow])
def kpi_table(
    db: DbSession,
    old_date: date = Query(default_factory=lambda: date.today() - timedelta(days=7)),
) -> list[KpiTableRow]:
    try:
        rows = ReportService(db).kpi_table(old_date)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return [KpiTableRow(**item) for item in rows]
