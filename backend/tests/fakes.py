"""In-memory stand-in for TicketRepository (same interface, same domain errors)."""

from datetime import UTC, date, datetime, timedelta

from app.domain.exceptions import (
    CommentEmpty,
    ConcurrencyConflict,
    OperatorNotFound,
    TicketClosed,
    TicketNotFound,
)
from app.domain.state_machine import TRANSITIONS, validate_transition
from app.domain.status import TicketStatus


class FakeTicketRepository:
    def __init__(self) -> None:
        self.operators = [
            {"id": 1, "name": "Ana Torres", "email": "ana@example.com"},
            {"id": 2, "name": "Luis Perez", "email": "luis@example.com"},
        ]
        self.tickets: dict[int, dict] = {}
        self.history: list[dict] = []
        self._next_ticket = 1001
        self._next_event = 1
        self._clock = datetime(2026, 1, 1, tzinfo=UTC)

    def _now(self) -> datetime:
        self._clock += timedelta(seconds=1)
        return self._clock

    def _event(self, ticket_id, event_type, from_status, to_status, comment, actor) -> dict:
        event = {
            "id": self._next_event,
            "ticket_id": ticket_id,
            "event_type": event_type,
            "from_status": from_status,
            "to_status": to_status,
            "comment": comment,
            "actor": actor,
            "created_at": self._now(),
        }
        self._next_event += 1
        self.history.append(event)
        return event

    def _operator_name(self, operator_id: int | None) -> str | None:
        return next((o["name"] for o in self.operators if o["id"] == operator_id), None)

    def _view(self, ticket: dict) -> dict:
        return {
            **ticket,
            "assigned_operator_name": self._operator_name(ticket["assigned_operator_id"]),
        }

    def _locked(self, ticket_id: int, expected_version: int) -> dict:
        ticket = self.tickets.get(ticket_id)
        if ticket is None:
            raise TicketNotFound()
        if ticket["version"] != expected_version:
            raise ConcurrencyConflict()
        return ticket

    def _touch(self, ticket: dict) -> None:
        ticket["version"] += 1
        ticket["updated_at"] = self._now()

    # writes

    def create_ticket(self, title, description, asset_code, priority, reported_by) -> dict:
        now = self._now()
        ticket = {
            "id": self._next_ticket,
            "title": title,
            "description": description,
            "asset_code": asset_code,
            "priority": priority,
            "status": "PENDING",
            "diagnosis": None,
            "assigned_operator_id": None,
            "reported_by": reported_by,
            "created_at": now,
            "updated_at": now,
            "version": 1,
        }
        self._next_ticket += 1
        self.tickets[ticket["id"]] = ticket
        self._event(ticket["id"], "CREATED", None, "PENDING", None, reported_by)
        return self._view(ticket)

    def change_status(self, ticket_id, to_status, diagnosis, comment, actor, expected_version):
        ticket = self._locked(ticket_id, expected_version)
        from_status = ticket["status"]
        validate_transition(TicketStatus(from_status), TicketStatus(to_status), diagnosis, comment)
        ticket["status"] = to_status
        ticket["diagnosis"] = diagnosis or ticket["diagnosis"]
        self._touch(ticket)
        text = comment or (f"Diagnosis: {diagnosis}" if diagnosis else None)
        self._event(ticket_id, "STATUS_CHANGED", from_status, to_status, text, actor)
        return self._view(ticket)

    def add_comment(self, ticket_id, comment, actor) -> dict:
        if ticket_id not in self.tickets:
            raise TicketNotFound()
        if not comment.strip():
            raise CommentEmpty()
        return self._event(ticket_id, "COMMENT", None, None, comment, actor)

    def assign(self, ticket_id, operator_id, actor, expected_version) -> dict:
        ticket = self._locked(ticket_id, expected_version)
        if ticket["status"] in ("RESOLVED", "CANCELLED"):
            raise TicketClosed()
        if operator_id is not None and not self.operator_exists(operator_id):
            raise OperatorNotFound()
        ticket["assigned_operator_id"] = operator_id
        self._touch(ticket)
        name = self._operator_name(operator_id)
        self._event(
            ticket_id,
            "ASSIGNED",
            None,
            None,
            f"Assigned to {name}" if name else "Unassigned",
            actor,
        )
        return self._view(ticket)

    # reads

    def get_ticket(self, ticket_id) -> dict | None:
        ticket = self.tickets.get(ticket_id)
        return self._view(ticket) if ticket else None

    def list_tickets(
        self, status=None, priority=None, operator_id=None, date_from=None, date_to=None, q=None
    ) -> list[dict]:
        rows = []
        for t in self.tickets.values():
            created: date = t["created_at"].date()
            if status and t["status"] != status:
                continue
            if priority and t["priority"] != priority:
                continue
            if operator_id is not None and t["assigned_operator_id"] != operator_id:
                continue
            if date_from and created < date_from:
                continue
            if date_to and created > date_to:
                continue
            if q and q.lower() not in f"{t['title']} {t['asset_code']} {t['id']}".lower():
                continue
            rows.append(self._view(t))
        return sorted(rows, key=lambda r: (r["created_at"], r["id"]), reverse=True)

    def get_history(self, ticket_id) -> list[dict]:
        return [e for e in self.history if e["ticket_id"] == ticket_id]

    def list_operators(self) -> list[dict]:
        return list(self.operators)

    def list_transitions(self) -> list[dict]:
        return [
            {
                "from_status": frm,
                "to_status": rule.to_status,
                "requires_diagnosis": rule.requires_diagnosis,
                "requires_comment": rule.requires_comment,
            }
            for frm, rules in TRANSITIONS.items()
            for rule in rules
        ]

    def list_notifications(self, since, limit) -> list[dict]:
        titles = {t["id"]: t["title"] for t in self.tickets.values()}
        events = [
            {
                "id": e["id"],
                "ticket_id": e["ticket_id"],
                "ticket_title": titles[e["ticket_id"]],
                "from_status": e["from_status"],
                "to_status": e["to_status"],
                "actor": e["actor"],
                "created_at": e["created_at"],
            }
            for e in self.history
            if e["event_type"] in ("STATUS_CHANGED", "ASSIGNED")
            and (since is None or e["created_at"] > since)
        ]
        return sorted(events, key=lambda e: (e["created_at"], e["id"]), reverse=True)[:limit]

    def operator_exists(self, operator_id) -> bool:
        return any(o["id"] == operator_id for o in self.operators)
