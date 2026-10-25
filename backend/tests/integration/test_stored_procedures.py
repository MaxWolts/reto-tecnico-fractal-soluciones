"""Integration tests for the MySQL stored procedures.

WARNING: these tests reset the database at TEST_DATABASE_URL (drop and
recreate all tables). Point it at a disposable database. DATABASE_URL is never
used, and the tests refuse to run when both URLs are equal.

Skipped automatically when TEST_DATABASE_URL is not set or MySQL is unreachable.
Run from backend/:  python -m pytest -q -m integration
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pymysql
import pytest
from pymysql.cursors import DictCursor

from scripts.init_db import InitDbError, init_db, parse_database_url
from tests.integration_guard import integration_env, resolve_test_database_url

pytestmark = pytest.mark.integration

ER_SIGNAL_EXCEPTION = 1644
ER_ROW_IS_REFERENCED_2 = 1451

TEST_DATABASE_URL = resolve_test_database_url(integration_env())
if not TEST_DATABASE_URL:
    pytest.skip("TEST_DATABASE_URL not set", allow_module_level=True)


@pytest.fixture(scope="module")
def conn() -> Iterator[pymysql.connections.Connection]:
    try:
        # creates the database when missing, so it must run before connect
        init_db(TEST_DATABASE_URL, seed=False, verbose=False)
    except InitDbError as exc:
        pytest.skip(f"MySQL unreachable: {exc}")
    params = parse_database_url(TEST_DATABASE_URL)
    try:
        connection = pymysql.connect(
            **params,
            charset="utf8mb4",
            autocommit=True,
            cursorclass=DictCursor,
            connect_timeout=5,
        )
    except pymysql.MySQLError as exc:
        pytest.skip(f"MySQL unreachable: {exc}")
    with connection:
        yield connection


def call(conn: pymysql.connections.Connection, proc: str, *args: Any) -> list[dict]:
    """CALL a procedure, return its first result set and drain the rest."""
    placeholders = ", ".join(["%s"] * len(args))
    with conn.cursor() as cur:
        cur.execute(f"CALL {proc}({placeholders})", args)
        rows = list(cur.fetchall())
        while cur.nextset():
            pass
    return rows


def query(conn: pymysql.connections.Connection, sql: str, *args: Any) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(sql, args)
        return list(cur.fetchall())


def history(conn: pymysql.connections.Connection, ticket_id: int) -> list[dict]:
    return query(conn, "SELECT * FROM ticket_history WHERE ticket_id = %s ORDER BY id", ticket_id)


def expect_signal(code: str, conn: pymysql.connections.Connection, proc: str, *args: Any):
    with pytest.raises(pymysql.MySQLError) as info:
        call(conn, proc, *args)
    assert info.value.args[0] == ER_SIGNAL_EXCEPTION
    assert info.value.args[1] == code


def create_ticket(conn: pymysql.connections.Connection) -> dict:
    rows = call(conn, "sp_create_ticket", "UPS alarm", "  ", "ATM-0001", None, "Ana Torres")
    assert len(rows) == 1
    return rows[0]


def test_create_ticket_returns_read_model_and_created_event(conn):
    ticket = create_ticket(conn)

    assert set(ticket) == {
        "id",
        "title",
        "description",
        "asset_code",
        "priority",
        "status",
        "diagnosis",
        "assigned_operator_id",
        "assigned_operator_name",
        "reported_by",
        "created_at",
        "updated_at",
        "version",
    }
    assert ticket["status"] == "PENDING"
    assert ticket["priority"] == "MEDIUM"
    assert ticket["description"] is None
    assert ticket["version"] == 1

    events = history(conn, ticket["id"])
    assert len(events) == 1
    assert events[0]["event_type"] == "CREATED"
    assert events[0]["to_status"] == "PENDING"
    assert events[0]["actor"] == "Ana Torres"


def test_status_flow_with_rollback_and_rules(conn):
    tid = create_ticket(conn)["id"]

    # PENDING -> RESOLVED is not allowed; nothing changes (rollback proof).
    expect_signal(
        "INVALID_TRANSITION", conn, "sp_change_ticket_status", tid, "RESOLVED", "x", None, "Op", 1
    )
    assert len(history(conn, tid)) == 1
    row = query(conn, "SELECT status, version FROM ticket WHERE id = %s", tid)[0]
    assert row == {"status": "PENDING", "version": 1}

    ticket = call(conn, "sp_change_ticket_status", tid, "IN_PROGRESS", None, None, "Op", 1)[0]
    assert ticket["status"] == "IN_PROGRESS"
    assert ticket["version"] == 2

    expect_signal(
        "DIAGNOSIS_REQUIRED", conn, "sp_change_ticket_status", tid, "RESOLVED", "   ", None, "Op", 2
    )

    ticket = call(
        conn, "sp_change_ticket_status", tid, "RESOLVED", " Battery replaced ", None, "Op", 2
    )[0]
    assert ticket["status"] == "RESOLVED"
    assert ticket["diagnosis"] == "Battery replaced"
    assert ticket["version"] == 3

    events = history(conn, tid)
    assert len(events) == 3
    assert events[-1]["event_type"] == "STATUS_CHANGED"
    assert events[-1]["from_status"] == "IN_PROGRESS"
    assert events[-1]["to_status"] == "RESOLVED"
    assert events[-1]["comment"] == "Diagnosis: Battery replaced"


def test_stale_version_is_conflict(conn):
    tid = create_ticket(conn)["id"]
    call(conn, "sp_change_ticket_status", tid, "IN_PROGRESS", None, None, "Op", 1)

    expect_signal(
        "CONCURRENCY_CONFLICT",
        conn,
        "sp_change_ticket_status",
        tid,
        "PENDING",
        None,
        "back",
        "Op",
        1,
    )
    assert len(history(conn, tid)) == 2


def test_unknown_ticket_is_not_found(conn):
    expect_signal(
        "TICKET_NOT_FOUND",
        conn,
        "sp_change_ticket_status",
        999999,
        "IN_PROGRESS",
        None,
        None,
        "Op",
        1,
    )


def test_blank_comment_is_empty(conn):
    tid = create_ticket(conn)["id"]
    expect_signal("COMMENT_EMPTY", conn, "sp_add_comment", tid, "   ", "Op")
    assert len(history(conn, tid)) == 1

    event = call(conn, "sp_add_comment", tid, " Parts ordered ", "Op")[0]
    assert event["event_type"] == "COMMENT"
    assert event["comment"] == "Parts ordered"


def test_assign_unknown_operator_is_not_found(conn):
    tid = create_ticket(conn)["id"]
    expect_signal("OPERATOR_NOT_FOUND", conn, "sp_assign_ticket", tid, 999999, "Op", 1)
    row = query(conn, "SELECT assigned_operator_id, version FROM ticket WHERE id = %s", tid)[0]
    assert row == {"assigned_operator_id": None, "version": 1}


def test_delete_ticket_with_history_is_restricted(conn):
    tid = create_ticket(conn)["id"]
    with pytest.raises(pymysql.MySQLError) as info:
        query(conn, "DELETE FROM ticket WHERE id = %s", tid)
    assert info.value.args[0] == ER_ROW_IS_REFERENCED_2
