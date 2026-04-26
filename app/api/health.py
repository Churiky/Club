from datetime import datetime

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "timestamp": datetime.utcnow()}


@router.get("/ready")
def ready() -> dict:
    return {"status": "ready", "timestamp": datetime.utcnow()}
