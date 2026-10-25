from collections.abc import Iterator
from urllib.parse import unquote, urlparse

import pymysql
from pymysql.connections import Connection
from pymysql.cursors import DictCursor

from app.config import get_settings
from app.errors import DatabaseUnavailable


def _connect_args(database_url: str) -> dict:
    """Parse mysql:// or mysql+pymysql:// URLs into PyMySQL keyword arguments."""
    url = urlparse(database_url)
    if url.scheme not in ("mysql", "mysql+pymysql"):
        raise ValueError(f"Unsupported database scheme: {url.scheme!r}")
    return {
        "host": url.hostname or "localhost",
        "port": url.port or 3306,
        "user": unquote(url.username or ""),
        "password": unquote(url.password or ""),
        "database": url.path.lstrip("/"),
    }


def open_connection() -> Connection:
    try:
        return pymysql.connect(
            **_connect_args(get_settings().database_url),
            charset="utf8mb4",
            cursorclass=DictCursor,
            autocommit=False,
            connect_timeout=5,
            init_command="SET time_zone = '+00:00'",
        )
    except pymysql.err.MySQLError as exc:
        raise DatabaseUnavailable(str(exc)) from exc


class LazyConnection:
    """Opens the real connection on first cursor use, so requests that fail
    validation never touch the database."""

    def __init__(self) -> None:
        self._conn: Connection | None = None

    def cursor(self, *args, **kwargs):
        if self._conn is None:
            self._conn = open_connection()
        return self._conn.cursor(*args, **kwargs)

    def commit(self) -> None:
        if self._conn is not None:
            self._conn.commit()

    def rollback(self) -> None:
        if self._conn is not None:
            self._conn.rollback()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None


def get_connection() -> Iterator[LazyConnection]:
    """FastAPI dependency: one lazy connection per request, closed if opened."""
    conn = LazyConnection()
    try:
        yield conn
    finally:
        conn.close()


def database_is_up() -> bool:
    try:
        conn = open_connection()
    except DatabaseUnavailable:
        return False
    try:
        conn.ping(reconnect=False)
        return True
    except pymysql.err.MySQLError:
        return False
    finally:
        conn.close()
