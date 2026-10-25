import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_service
from app.main import create_app
from app.services.ticket_service import TicketService
from tests.fakes import FakeTicketRepository

NEW_TICKET = {
    "title": "Broken pump",
    "assetCode": "PUMP-01",
    "priority": "HIGH",
    "reportedBy": "Maria",
}


@pytest.fixture
def app():
    app = create_app()
    service = TicketService(FakeTicketRepository())
    app.dependency_overrides[get_service] = lambda: service
    return app


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def create(client) -> dict:
    return client.post("/api/tickets", json=NEW_TICKET).json()


def move(client, ticket_id, to, version, **extra):
    body = {"toStatus": to, "actor": "Ana", "version": version, **extra}
    return client.post(f"/api/tickets/{ticket_id}/transitions", json=body)


def test_create_201(client):
    r = client.post("/api/tickets", json=NEW_TICKET)
    assert r.status_code == 201
    body = r.json()
    assert body["code"] == "#1001"
    assert body["assetCode"] == "PUMP-01"
    assert body["status"] == "PENDING"
    assert body["assignedOperator"] is None
    assert body["version"] == 1
    assert [t["toStatus"] for t in body["allowedTransitions"]] == ["IN_PROGRESS", "CANCELLED"]


def test_create_validation_400_shape(client):
    r = client.post("/api/tickets", json={**NEW_TICKET, "assetCode": "bad code", "title": "x"})
    assert r.status_code == 400
    assert r.headers["content-type"].startswith("application/problem+json")
    body = r.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert body["status"] == 400
    assert {e["field"] for e in body["errors"]} == {"assetCode", "title"}
    assert all("message" in e for e in body["errors"])


def test_get_404(client):
    r = client.get("/api/tickets/9999")
    assert r.status_code == 404
    assert r.json()["code"] == "TICKET_NOT_FOUND"
    assert r.headers["content-type"].startswith("application/problem+json")


def test_unknown_route_is_problem(client):
    r = client.get("/api/nope")
    assert r.status_code == 404
    assert r.json()["status"] == 404


def test_stale_version_409(client):
    t = create(client)
    r = move(client, t["id"], "IN_PROGRESS", 5)
    assert r.status_code == 409
    assert r.json()["code"] == "CONCURRENCY_CONFLICT"


def test_pending_to_resolved_422(client):
    t = create(client)
    r = move(client, t["id"], "RESOLVED", 1, diagnosis="x")
    assert r.status_code == 422
    assert r.json()["code"] == "INVALID_TRANSITION"


def test_missing_diagnosis_422(client):
    t = create(client)
    move(client, t["id"], "IN_PROGRESS", 1)
    r = move(client, t["id"], "RESOLVED", 2)
    assert r.status_code == 422
    assert r.json()["code"] == "DIAGNOSIS_REQUIRED"


def test_happy_path_and_history(client):
    t = create(client)
    assert move(client, t["id"], "IN_PROGRESS", 1).json()["status"] == "IN_PROGRESS"
    r = move(client, t["id"], "RESOLVED", 2, diagnosis="Seal replaced")
    assert r.status_code == 200
    assert r.json()["status"] == "RESOLVED"
    assert r.json()["diagnosis"] == "Seal replaced"
    assert r.json()["allowedTransitions"] == []
    history = client.get(f"/api/tickets/{t['id']}/history").json()
    assert len(history) == 3
    assert [h["eventType"] for h in history] == ["CREATED", "STATUS_CHANGED", "STATUS_CHANGED"]
    assert history[1]["fromStatus"] == "PENDING"
    assert history[1]["toStatus"] == "IN_PROGRESS"


def test_history_404(client):
    assert client.get("/api/tickets/1/history").status_code == 404


def test_comment_201_and_blank_400(client):
    t = create(client)
    r = client.post(f"/api/tickets/{t['id']}/comments", json={"comment": "On it", "actor": "Ana"})
    assert r.status_code == 201
    assert r.json()["eventType"] == "COMMENT"
    assert r.json()["ticketId"] == t["id"]
    blank = client.post(f"/api/tickets/{t['id']}/comments", json={"comment": "  ", "actor": "Ana"})
    assert blank.status_code == 400
    assert blank.json()["errors"][0]["field"] == "comment"


def test_assign_and_unassign(client):
    t = create(client)
    url = f"/api/tickets/{t['id']}/assignee"
    r = client.put(url, json={"operatorId": 1, "actor": "Ana", "version": 1})
    assert r.status_code == 200
    assert r.json()["assignedOperator"] == {"id": 1, "name": "Ana Torres"}
    r = client.put(url, json={"operatorId": None, "actor": "Ana", "version": 2})
    assert r.json()["assignedOperator"] is None


def test_assign_closed_ticket_422(client):
    t = create(client)
    assert move(client, t["id"], "CANCELLED", 1, comment="dup").status_code == 200
    r = client.put(
        f"/api/tickets/{t['id']}/assignee", json={"operatorId": 1, "actor": "Ana", "version": 2}
    )
    assert r.status_code == 422
    assert r.json()["code"] == "TICKET_CLOSED"


def test_version_out_of_range_400(client):
    t = create(client)
    r = move(client, t["id"], "IN_PROGRESS", 2_147_483_648)
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "version"


def test_assign_unknown_operator_404(client):
    t = create(client)
    r = client.put(
        f"/api/tickets/{t['id']}/assignee", json={"operatorId": 99, "actor": "Ana", "version": 1}
    )
    assert r.status_code == 404
    assert r.json()["code"] == "OPERATOR_NOT_FOUND"


def test_list_with_filters(client):
    a = create(client)
    create(client)
    move(client, a["id"], "IN_PROGRESS", 1)
    assert len(client.get("/api/tickets").json()) == 2
    r = client.get("/api/tickets", params={"status": "IN_PROGRESS"})
    assert [t["id"] for t in r.json()] == [a["id"]]
    assert client.get("/api/tickets", params={"status": "BOGUS"}).status_code == 400


def test_operators_and_transitions(client):
    ops = client.get("/api/operators").json()
    assert ops[0] == {"id": 1, "name": "Ana Torres", "email": "ana@example.com"}
    transitions = client.get("/api/transitions").json()
    assert len(transitions) == 5
    assert {"fromStatus", "toStatus", "requiresDiagnosis", "requiresComment"} == set(transitions[0])


def test_notifications(client):
    t = create(client)
    move(client, t["id"], "IN_PROGRESS", 1)
    r = client.get("/api/notifications", params={"limit": 5})
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    assert body[0]["ticketTitle"] == "Broken pump"
    assert body[0]["toStatus"] == "IN_PROGRESS"
    since = body[0]["createdAt"]
    assert client.get("/api/notifications", params={"since": since}).json() == []


def test_unhandled_error_is_generic_500(app):
    def boom():
        raise RuntimeError("secret internal detail")

    app.dependency_overrides[get_service] = boom
    r = TestClient(app, raise_server_exceptions=False).get("/api/tickets")
    assert r.status_code == 500
    body = r.json()
    assert body["code"] == "INTERNAL_ERROR"
    assert "secret" not in r.text
    assert "Traceback" not in r.text
