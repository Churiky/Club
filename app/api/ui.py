from fastapi import APIRouter
from fastapi.responses import FileResponse


router = APIRouter(tags=["ui"])


@router.get("/")
def home() -> FileResponse:
    return FileResponse("app/static/index.html")


@router.get("/dashboard")
def dashboard() -> FileResponse:
    return FileResponse("app/static/index.html")
