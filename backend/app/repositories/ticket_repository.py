"""All SQL lives here. Writes go through stored procedures; reads use parameterized SELECTs."""

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, date, datetime, timedelta

import pymysql

from app.domain.exceptions import CODE_TO_ERROR
from app.errors import DatabaseUnavailable, DataRejected

_SIGNAL_ERRNO = 1644
_DATA_REJECTED_ERRNOS = {3819, 1406}
_UNAVAILABLE_ERRNOS = {0, 2002, 2003, 2006, 2013, 2055}

_TICKET_SELECT = """
SELECT t.id, t.title, t.description, t.asset_code, t.priority, t.status, t.diagnosis,
       t.assigned_operator_id, o.name AS assigned_operator_name, t.reported_by,
       t.created_at, t.updated_at, t.version
FROM ticket t
LEFT JOIN operator o ON o.id = t.assigned_operator_id
"""

_HISTORY_COLUMNS = "id, ticket_id, event_type, from_status, to_status, comment, actor, created_at"


def _translate(exc: pymysql.err.MySQLError) -> Exception:
    errno = exc.args[0] if exc.args and isinstance(exc.args[0], int) else 0
    message = str(exc.args[1]) if len(exc.args) > 1 else ""
    if errno == _SIGNAL_ERRNO and message in CODE_TO_ERROR:
        return CODE_TO_ERROR[message]()
    if errno in _DATA_REJECTED_ERRNOS:
        return DataRejected(message)
    if errno in _UNAVAILABLE_ERRNOS or isinstance(exc, pymysql.err.InterfaceError):
        return DatabaseUnavailable(message)
    return exc


def _as_utc(row: dict) -> dict:
    """The connection runs in UTC; mark naive datetimes as such."""
    return {
        key: value.replace(tzinfo=UTC) if isinstance(value, datetime) else value
        for key, value in row.items()
    }


def _like(text: str) -> str:
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


class TicketRepository:
    def __init__(self, conn: pymysql.connections.Connection) -> None:
        self._conn = conn

    @contextmanager
    def _guard(self) -> Iterator[None]:
        try:
            yield
        except pymysql.err.MySQLError as exc:
            try:
                self._conn.rollback()
            except pymysql.err.MySQLError:
                pass
            translated = _translate(exc)
            if translated is exc:
                raise
            raise translated from exc

    def _call(self, procedure: str, args: tuple) -> list[dict]:
        """Run a write stored procedure, drain its result sets and commit."""
        with self._guard():
            with self._conn.cursor() as cur:
                cur.callproc(procedure, args)
                rows = list(cur.fetchall())
                while cur.nextset():
                    pass
            self._conn.commit()
        return [_as_utc(r) for r in rows]

    def _select(self, sql: str, params: tuple = ()) -> list[dict]:
        with self._guard(), self._conn.cursor() as cur:
            cur.execute(sql, params)
            rows = list(cur.fetchall())
        return [_as_utc(r) for r in rows]

    # writes

    def create_ticket(
        self,
        title: str,
        description: str | None,
        asset_code: str,
        priority: str,
        reported_by: str,
    ) -> dict:
        args = (title, description, asset_code, priority, reported_by)
        return self._call("sp_create_ticket", args)[0]

    def change_status(
        self,
        ticket_id: int,
        to_status: str,
        diagnosis: str | None,
        comment: str | None,
        actor: str,
        expected_version: int,
    ) -> dict:
        args = (ticket_id, to_status, diagnosis, comment, actor, expected_version)
        return self._call("sp_change_ticket_status", args)[0]

    def add_comment(self, ticket_id: int, comment: str, actor: str) -> dict:
        return self._call("sp_add_comment", (ticket_id, comment, actor))[0]

    def assign(
        self, ticket_id: int, operator_id: int | None, actor: str, expected_version: int
    ) -> dict:
        args = (ticket_id, operator_id, actor, expected_version)
        return self._call("sp_assign_ticket", args)[0]

    # reads

    def get_ticket(self, ticket_id: int) -> dict | None:
        rows = self._select(_TICKET_SELECT + " WHERE t.id = %s", (ticket_id,))
        return rows[0] if rows else None

    def list_tickets(
        self,
        status: str | None = None,
        priority: str | None = None,
        operator_id: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        q: str | None = None,
    ) -> list[dict]:
        clauses: list[str] = []
        params: list = []
        if status:
            clauses.append("t.status = %s")
            params.append(status)
        if priority:
            clauses.append("t.priority = %s")
            params.append(priority)
        if operator_id is not None:
            clauses.append("t.assigned_operator_id = %s")
            params.append(operator_id)
        if date_from:
            clauses.append("t.created_at >= %s")
            params.append(date_from)
        if date_to:
            clauses.append("t.created_at < %s")
            params.append(
                datetime.combine(date_to, datetime.min.time()) + timedelta(days=1)
                if date_to < date.max
                else datetime.max
            )
        if q:
            clauses.append(
                "(t.title LIKE %s OR t.asset_code LIKE %s OR CAST(t.id AS CHAR) LIKE %s)"
            )
            params.extend([_like(q)] * 3)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        return self._select(
            _TICKET_SELECT + where + " ORDER BY t.created_at DESC, t.id DESC", tuple(params)
        )

    def get_history(self, ticket_id: int) -> list[dict]:
        return self._select(
            f"SELECT {_HISTORY_COLUMNS} FROM ticket_history WHERE ticket_id = %s "
            "ORDER BY created_at ASC, id ASC",
            (ticket_id,),
        )

    def list_operators(self) -> list[dict]:
        return self._select("SELECT id, name, email FROM operator ORDER BY name, id")

    def list_transitions(self) -> list[dict]:
        rows = self._select(
            "SELECT from_status, to_status, requires_diagnosis, requires_comment "
            "FROM allowed_transition ORDER BY from_status, to_status"
        )
        for row in rows:
            row["requires_diagnosis"] = bool(row["requires_diagnosis"])
            row["requires_comment"] = bool(row["requires_comment"])
        return rows

    def list_notifications(self, since: datetime | None, limit: int) -> list[dict]:
        clauses = ["h.event_type IN ('STATUS_CHANGED', 'ASSIGNED')"]
        params: list = []
        if since is not None:
            clauses.append("h.created_at > %s")
            try:
                aware = since.replace(tzinfo=UTC) if since.tzinfo is None else since.astimezone(UTC)
            except OverflowError:
                aware = since.replace(tzinfo=UTC)
            params.append(aware.replace(tzinfo=None))
        params.append(limit)
        return self._select(
            "SELECT h.id, h.ticket_id, t.title AS ticket_title, h.from_status, h.to_status, "
            "h.actor, h.created_at "
            "FROM ticket_history h JOIN ticket t ON t.id = h.ticket_id "
            f"WHERE {' AND '.join(clauses)} "
            "ORDER BY h.created_at DESC, h.id DESC LIMIT %s",
            tuple(params),
        )

    def operator_exists(self, operator_id: int) -> bool:
        return bool(self._select("SELECT 1 AS ok FROM operator WHERE id = %s", (operator_id,)))
