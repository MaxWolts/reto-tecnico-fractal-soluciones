from fastapi import APIRouter, Depends

from app.api.deps import get_service
from app.schemas.ticket import OperatorOut
from app.services.ticket_service import TicketService

router = APIRouter(prefix="/api", tags=["operators"])


@router.get("/operators", response_model=list[OperatorOut])
def list_operators(service: TicketService = Depends(get_service)):
    return service.operators()
