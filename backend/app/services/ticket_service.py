"""Business use cases. Returns plain dicts shaped like the API models (snake_case keys)."""

from datetime import date, datetime

from app.domain.exceptions import (
    CommentEmpty,
    ConcurrencyConflict,
    OperatorNotFound,
    TicketClosed,
    TicketNotFound,
)
from app.domain.state_machine import allowed_from, validate_transition
from app.domain.status import Priority, TicketStatus


def _clean(text: str | None) -> str | None:
    text = (text or "").strip()
    return text or None


def _to_ticket(row: dict) -> dict:
    status = TicketStatus(row["status"])
    operator_id = row["assigned_operator_id"]
    return {
        "id": row["id"],
        "code": f"#{row['id']}",
        "title": row["title"],
        "description": row["description"],
        "asset_code": row["asset_code"],
        "priority": row["priority"],
        "status": row["status"],
        "diagnosis": row["diagnosis"],
        "assigned_operator": (
            {"id": operator_id, "name": row["assigned_operator_name"]}
            if operator_id is not None
            else None
        ),
        "reported_by": row["reported_by"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "version": row["version"],
        "allowed_transitions": [
            {
                "to_status": rule.to_status,
                "requires_diagnosis": rule.requires_diagnosis,
                "requires_comment": rule.requires_comment,
            }
            for rule in allowed_from(status)
        ],
    }


class TicketService:
    def __init__(self, repo) -> None:
        self._repo = repo

    def _require(self, ticket_id: int) -> dict:
        row = self._repo.get_ticket(ticket_id)
        if row is None:
            raise TicketNotFound()
        return row

    def create(
        self,
        title: str,
        description: str | None,
        asset_code: str,
        priority: Priority,
        reported_by: str,
    ) -> dict:
        row = self._repo.create_ticket(
            title.strip(), _clean(description), asset_code, str(priority), reported_by.strip()
        )
        return _to_ticket(row)

    def get(self, ticket_id: int) -> dict:
        return _to_ticket(self._require(ticket_id))

    def list_tickets(
        self,
        status: TicketStatus | None = None,
        priority: Priority | None = None,
        operator_id: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        q: str | None = None,
    ) -> list[dict]:
        rows = self._repo.list_tickets(
            status=str(status) if status else None,
            priority=str(priority) if priority else None,
            operator_id=operator_id,
            date_from=date_from,
            date_to=date_to,
            q=_clean((q or "").strip().lstrip("#")),
        )
        return [_to_ticket(r) for r in rows]

    def history(self, ticket_id: int) -> list[dict]:
        self._require(ticket_id)
        return self._repo.get_history(ticket_id)

    def change_status(
        self,
        ticket_id: int,
        to_status: TicketStatus,
        diagnosis: str | None,
        comment: str | None,
        actor: str,
        version: int,
    ) -> dict:
        current = self._require(ticket_id)
        if current["version"] != version:
            raise ConcurrencyConflict()
        diagnosis, comment = _clean(diagnosis), _clean(comment)
        validate_transition(TicketStatus(current["status"]), to_status, diagnosis, comment)
        row = self._repo.change_status(
            ticket_id, str(to_status), diagnosis, comment, actor.strip(), version
        )
        return _to_ticket(row)

    def add_comment(self, ticket_id: int, comment: str, actor: str) -> dict:
        self._require(ticket_id)
        text = _clean(comment)
        if text is None:
            raise CommentEmpty()
        return self._repo.add_comment(ticket_id, text, actor.strip())

    def assign(self, ticket_id: int, operator_id: int | None, actor: str, version: int) -> dict:
        current = self._require(ticket_id)
        if TicketStatus(current["status"]) in (TicketStatus.RESOLVED, TicketStatus.CANCELLED):
            raise TicketClosed()
        if operator_id is not None and not self._repo.operator_exists(operator_id):
            raise OperatorNotFound()
        row = self._repo.assign(ticket_id, operator_id, actor.strip(), version)
        return _to_ticket(row)

    def operators(self) -> list[dict]:
        return self._repo.list_operators()

    def transitions(self) -> list[dict]:
        return self._repo.list_transitions()

    def notifications(self, since: datetime | None, limit: int) -> list[dict]:
        return self._repo.list_notifications(since, limit)
