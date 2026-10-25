import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient

import app.db as db
from app.db import LazyConnection
from app.errors import DatabaseUnavailable
from app.main import create_app
from tests.integration_guard import UnsafeTestDatabase, resolve_test_database_url


def test_test_url_unset_returns_none():
    assert resolve_test_database_url({"DATABASE_URL": "mysql://a@h/prod"}) is None


def test_test_url_never_falls_back_to_database_url():
    assert (
        resolve_test_database_url({"DATABASE_URL": "mysql://a@h/prod", "TEST_DATABASE_URL": ""})
        is None
    )


def test_test_url_equal_to_database_url_refused():
    env = {"DATABASE_URL": "mysql://a@h/prod", "TEST_DATABASE_URL": "mysql://a@h/prod"}
    with pytest.raises(UnsafeTestDatabase):
        resolve_test_database_url(env)


def test_test_url_distinct_accepted():
    env = {"DATABASE_URL": "mysql://a@h/prod", "TEST_DATABASE_URL": "mysql://a@h/test"}
    assert resolve_test_database_url(env) == "mysql://a@h/test"


def test_500_has_cors_headers_and_problem_json():
    app = create_app()
    router = APIRouter()

    @router.get("/boom")
    def boom():
        raise RuntimeError("kaboom")

    app.include_router(router)
    client = TestClient(app, raise_server_exceptions=False)
    origin = "http://localhost:5173"
    r = client.get("/boom", headers={"Origin": origin})
    assert r.status_code == 500
    assert r.headers["access-control-allow-origin"] == origin
    assert r.headers["content-type"].startswith("application/problem+json")
    assert r.json()["code"] == "INTERNAL_ERROR"


def test_validation_400_before_db_when_db_down(monkeypatch):
    def down():
        raise DatabaseUnavailable("down")

    monkeypatch.setattr(db, "open_connection", down)
    client = TestClient(create_app(), raise_server_exceptions=False)
    r = client.get("/api/tickets?status=BAD")
    assert r.status_code == 400
    assert r.json()["code"] == "VALIDATION_ERROR"


def test_lazy_connection_close_without_open_is_noop(monkeypatch):
    monkeypatch.setattr(db, "open_connection", lambda: pytest.fail("opened"))
    conn = LazyConnection()
    conn.commit()
    conn.rollback()
    conn.close()
