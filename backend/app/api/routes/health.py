from fastapi import APIRouter

from app.db import database_is_up

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "database": "ok" if database_is_up() else "down"}
