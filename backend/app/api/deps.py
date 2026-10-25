from fastapi import Depends
from pymysql.connections import Connection

from app.db import get_connection
from app.repositories.ticket_repository import TicketRepository
from app.services.ticket_service import TicketService


def get_service(conn: Connection = Depends(get_connection)) -> TicketService:
    return TicketService(TicketRepository(conn))
