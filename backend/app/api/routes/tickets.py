from datetime import date

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_service
from app.domain.status import Priority, TicketStatus
from app.schemas.ticket import (
    AddCommentRequest,
    AssignRequest,
    ChangeStatusRequest,
    CreateTicketRequest,
    HistoryEventOut,
    TicketOut,
    TransitionOut,
)
from app.services.ticket_service import TicketService

router = APIRouter(prefix="/api", tags=["tickets"])


@router.get("/transitions", response_model=list[TransitionOut])
def list_transitions(service: TicketService = Depends(get_service)):
    return service.transitions()


@router.post("/tickets", response_model=TicketOut, status_code=201)
def create_ticket(body: CreateTicketRequest, service: TicketService = Depends(get_service)):
    return service.create(
        body.title, body.description, body.asset_code, body.priority, body.reported_by
    )


@router.get("/tickets", response_model=list[TicketOut])
def list_tickets(
    status: TicketStatus | None = None,
    priority: Priority | None = None,
    operator_id: int | None = Query(None, alias="operatorId"),
    date_from: date | None = Query(None, alias="from"),
    date_to: date | None = Query(None, alias="to"),
    q: str | None = Query(None, max_length=100),
    service: TicketService = Depends(get_service),
):
    return service.list_tickets(status, priority, operator_id, date_from, date_to, q)


@router.get("/tickets/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int, service: TicketService = Depends(get_service)):
    return service.get(ticket_id)


@router.get("/tickets/{ticket_id}/history", response_model=list[HistoryEventOut])
def get_history(ticket_id: int, service: TicketService = Depends(get_service)):
    return service.history(ticket_id)


@router.post("/tickets/{ticket_id}/transitions", response_model=TicketOut)
def change_status(
    ticket_id: int, body: ChangeStatusRequest, service: TicketService = Depends(get_service)
):
    return service.change_status(
        ticket_id, body.to_status, body.diagnosis, body.comment, body.actor, body.version
    )


@router.post("/tickets/{ticket_id}/comments", response_model=HistoryEventOut, status_code=201)
def add_comment(
    ticket_id: int, body: AddCommentRequest, service: TicketService = Depends(get_service)
):
    return service.add_comment(ticket_id, body.comment, body.actor)


@router.put("/tickets/{ticket_id}/assignee", response_model=TicketOut)
def assign(ticket_id: int, body: AssignRequest, service: TicketService = Depends(get_service)):
    return service.assign(ticket_id, body.operator_id, body.actor, body.version)
