from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.exceptions import RequestValidationError
from pydantic import AfterValidator

from app.api.deps import get_service
from app.domain.limits import check_date
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

BoundedDate = Annotated[date, AfterValidator(check_date)]


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
    date_from: BoundedDate | None = Query(None, alias="from"),
    date_to: BoundedDate | None = Query(None, alias="to"),
    q: str | None = Query(None, max_length=100),
    service: TicketService = Depends(get_service),
):
    if date_from and date_to and date_from > date_to:
        detail = {"loc": ("query", "from"), "msg": "'from' must not be after 'to'"}
        raise RequestValidationError([{**detail, "type": "value_error"}])
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
