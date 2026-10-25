"""Integration tests driving TicketRepository against MySQL (callproc path).

WARNING: these tests reset the database at TEST_DATABASE_URL (drop and
recreate all tables). Point it at a disposable database. DATABASE_URL is never
used, and the tests refuse to run when both URLs are equal.

Skipped automatically when TEST_DATABASE_URL is not set or MySQL is unreachable.
Run from backend/:  python -m pytest -q -m integration
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pymysql
import pytest
from pymysql.cursors import DictCursor

from app.domain.exceptions import InvalidTransition, TicketClosed
from app.repositories.ticket_repository import TicketRepository
from scripts.init_db import init_db, parse_database_url
from tests.integration_guard import resolve_test_database_url

pytestmark = pytest.mark.integration

TEST_DATABASE_URL = resolve_test_database_url(os.environ)
if not TEST_DATABASE_URL:
    pytest.skip("TEST_DATABASE_URL not set", allow_module_level=True)


@pytest.fixture(scope="module")
def repo() -> Iterator[TicketRepository]:
    params = parse_database_url(TEST_DATABASE_URL)
    try:
        connection = pymysql.connect(
            **params,
            charset="utf8mb4",
            autocommit=False,
            cursorclass=DictCursor,
            connect_timeout=5,
        )
    except pymysql.MySQLError as exc:
        pytest.skip(f"MySQL unreachable: {exc}")
    init_db(TEST_DATABASE_URL, seed=False, verbose=False)
    with connection:
        # seed=False leaves no operators; add one through the same connection
        with connection.cursor() as cur:
            cur.execute("INSERT INTO operator (name, email) VALUES ('Ana Torres', 'ana@test.io')")
        connection.commit()
        yield TicketRepository(connection)


def new_ticket(repo: TicketRepository) -> dict:
    return repo.create_ticket("UPS alarm", None, "ATM-0001", "HIGH", "Maria")


def test_create_ticket(repo):
    ticket = new_ticket(repo)
    assert ticket["status"] == "PENDING"
    assert ticket["version"] == 1
    assert ticket["priority"] == "HIGH"
    assert ticket["created_at"].tzinfo is not None


def test_change_status_ok(repo):
    ticket = new_ticket(repo)
    row = repo.change_status(ticket["id"], "IN_PROGRESS", None, None, "Ana", 1)
    assert row["status"] == "IN_PROGRESS"
    assert row["version"] == 2


def test_change_status_invalid_transition(repo):
    ticket = new_ticket(repo)
    with pytest.raises(InvalidTransition):
        repo.change_status(ticket["id"], "RESOLVED", "x", None, "Ana", 1)


def test_assign_and_add_comment_and_history_count(repo):
    ticket = new_ticket(repo)
    operator_id = repo.list_operators()[0]["id"]
    row = repo.assign(ticket["id"], operator_id, "Ana", 1)
    assert row["assigned_operator_id"] == operator_id
    assert row["assigned_operator_name"] == "Ana Torres"
    event = repo.add_comment(ticket["id"], "On it", "Ana")
    assert event["event_type"] == "COMMENT"
    assert len(repo.get_history(ticket["id"])) == 3  # CREATED, ASSIGNED, COMMENT


def test_assign_closed_ticket(repo):
    ticket = new_ticket(repo)
    repo.change_status(ticket["id"], "CANCELLED", None, "duplicate", "Ana", 1)
    with pytest.raises(TicketClosed):
        repo.assign(ticket["id"], None, "Ana", 2)
