from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_service
from app.schemas.ticket import NotificationOut
from app.services.ticket_service import TicketService

router = APIRouter(prefix="/api", tags=["notifications"])


@router.get("/notifications", response_model=list[NotificationOut])
def list_notifications(
    since: datetime | None = None,
    limit: int = Query(20, ge=1, le=100),
    service: TicketService = Depends(get_service),
):
    return service.notifications(since, limit)
