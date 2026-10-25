import pytest

from app.domain.exceptions import (
    CommentEmpty,
    CommentRequired,
    ConcurrencyConflict,
    DiagnosisRequired,
    InvalidTransition,
    OperatorNotFound,
    TicketNotFound,
)
from app.domain.status import Priority
from app.domain.status import TicketStatus as S
from app.services.ticket_service import TicketService
from tests.fakes import FakeTicketRepository


@pytest.fixture
def service() -> TicketService:
    return TicketService(FakeTicketRepository())


@pytest.fixture
def ticket(service) -> dict:
    return service.create("Broken pump", "  leaks  ", "PUMP-01", Priority.HIGH, " Maria ")


def test_create_builds_code_and_transitions(ticket):
    assert ticket["id"] == 1001
    assert ticket["code"] == "#1001"
    assert ticket["status"] == "PENDING"
    assert ticket["description"] == "leaks"
    assert ticket["reported_by"] == "Maria"
    assert ticket["assigned_operator"] is None
    assert [t["to_status"] for t in ticket["allowed_transitions"]] == [
        S.IN_PROGRESS,
        S.CANCELLED,
    ]


def test_blank_description_becomes_none(service):
    t = service.create("Broken pump", "   ", "PUMP-01", Priority.LOW, "Maria")
    assert t["description"] is None


def test_get_missing_raises(service):
    with pytest.raises(TicketNotFound):
        service.get(1)


def test_history_missing_ticket_raises(service):
    with pytest.raises(TicketNotFound):
        service.history(1)


def test_list_filters_by_status(service, ticket):
    other = service.create("Other", None, "AB", Priority.LOW, "Maria")
    service.change_status(other["id"], S.IN_PROGRESS, None, None, "Ana", other["version"])
    assert [t["id"] for t in service.list_tickets(status=S.IN_PROGRESS)] == [other["id"]]
    assert len(service.list_tickets()) == 2


def test_happy_path_history(service, ticket):
    t = service.change_status(ticket["id"], S.IN_PROGRESS, None, None, "Ana", 1)
    assert t["version"] == 2
    t = service.change_status(ticket["id"], S.RESOLVED, " replaced seal ", None, "Ana", 2)
    assert t["status"] == "RESOLVED"
    assert t["diagnosis"] == "replaced seal"
    assert t["allowed_transitions"] == []
    assert len(service.history(ticket["id"])) == 3


def test_pending_to_resolved_invalid(service, ticket):
    with pytest.raises(InvalidTransition):
        service.change_status(ticket["id"], S.RESOLVED, "x", None, "Ana", 1)


def test_missing_diagnosis(service, ticket):
    service.change_status(ticket["id"], S.IN_PROGRESS, None, None, "Ana", 1)
    with pytest.raises(DiagnosisRequired):
        service.change_status(ticket["id"], S.RESOLVED, "   ", None, "Ana", 2)


def test_cancel_requires_comment(service, ticket):
    with pytest.raises(CommentRequired):
        service.change_status(ticket["id"], S.CANCELLED, None, None, "Ana", 1)


def test_stale_version_conflict(service, ticket):
    with pytest.raises(ConcurrencyConflict):
        service.change_status(ticket["id"], S.IN_PROGRESS, None, None, "Ana", 7)


def test_change_status_missing_ticket(service):
    with pytest.raises(TicketNotFound):
        service.change_status(5, S.IN_PROGRESS, None, None, "Ana", 1)


def test_comment_blank_rejected(service, ticket):
    with pytest.raises(CommentEmpty):
        service.add_comment(ticket["id"], "   ", "Ana")


def test_comment_added(service, ticket):
    event = service.add_comment(ticket["id"], " hello ", "Ana")
    assert event["event_type"] == "COMMENT"
    assert event["comment"] == "hello"


def test_assign_and_unassign(service, ticket):
    t = service.assign(ticket["id"], 1, "Ana", 1)
    assert t["assigned_operator"] == {"id": 1, "name": "Ana Torres"}
    t = service.assign(ticket["id"], None, "Ana", 2)
    assert t["assigned_operator"] is None


def test_assign_unknown_operator(service, ticket):
    with pytest.raises(OperatorNotFound):
        service.assign(ticket["id"], 99, "Ana", 1)


def test_notifications_newest_first_with_limit(service, ticket):
    service.change_status(ticket["id"], S.IN_PROGRESS, None, None, "Ana", 1)
    service.assign(ticket["id"], 1, "Ana", 2)
    notes = service.notifications(None, 20)
    assert [n["id"] for n in notes] == [3, 2]
    assert len(service.notifications(None, 1)) == 1
    assert service.notifications(notes[0]["created_at"], 20) == []
