from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.manual_updates import router as manual_updates_router
from app.api.members import router as members_router
from app.api.reports import router as reports_router
from app.api.sync import router as sync_router
from app.api.ui import router as ui_router
from app.config import get_settings
from app.jobs.scheduler import shutdown_scheduler, start_scheduler


settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    start_scheduler(settings)
    yield
    shutdown_scheduler()


app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    lifespan=lifespan,
)

app.include_router(ui_router)
app.include_router(health_router)
app.include_router(members_router)
app.include_router(manual_updates_router)
app.include_router(sync_router)
app.include_router(reports_router)
