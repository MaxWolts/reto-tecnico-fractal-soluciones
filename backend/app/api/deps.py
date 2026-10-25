from fastapi import Depends

from app.db import LazyConnection, get_connection
from app.repositories.ticket_repository import TicketRepository
from app.services.ticket_service import TicketService


def get_service(conn: LazyConnection = Depends(get_connection)) -> TicketService:
    return TicketService(TicketRepository(conn))
