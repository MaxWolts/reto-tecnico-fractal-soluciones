import logging
import os
import ssl
import tempfile
from collections.abc import Iterator
from urllib.parse import parse_qs, unquote, urlparse

import pymysql
from pymysql.connections import Connection
from pymysql.cursors import DictCursor

from app.config import get_settings
from app.errors import DatabaseUnavailable

logger = logging.getLogger(__name__)

_SSL_MODES = {"REQUIRED", "VERIFY_CA", "VERIFY_IDENTITY"}
_ca_file_cache: dict[str, str] = {}
_warned_unverified = False


def _ssl_mode(query: str) -> str | None:
    """Return the upper-cased ssl-mode from a URL query string, if any."""
    values = parse_qs(query)
    for key in ("ssl-mode", "ssl_mode"):
        if values.get(key):
            return values[key][-1].strip().upper()
    return None


def _ca_file() -> str | None:
    """Return a CA file path from DB_SSL_CA_PATH, or from DB_SSL_CA (PEM text)."""
    path = os.environ.get("DB_SSL_CA_PATH", "").strip()
    if path:
        return path
    pem = os.environ.get("DB_SSL_CA", "").strip()
    if not pem:
        return None
    if pem not in _ca_file_cache:
        handle = tempfile.NamedTemporaryFile(
            "w", suffix=".pem", prefix="db-ca-", delete=False, encoding="utf-8"
        )
        with handle:
            handle.write(pem + "\n")
        _ca_file_cache[pem] = handle.name
    return _ca_file_cache[pem]


def _ssl_context(mode: str | None) -> ssl.SSLContext | None:
    """Build the TLS context for an ssl-mode, or None for a plain connection."""
    global _warned_unverified
    if mode not in _SSL_MODES:
        return None
    ca = _ca_file()
    if ca:
        ctx = ssl.create_default_context(cafile=ca)
        ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
        ctx.check_hostname = mode == "VERIFY_IDENTITY"
        ctx.verify_mode = ssl.CERT_REQUIRED
        return ctx
    if not _warned_unverified:
        _warned_unverified = True
        logger.warning(
            "ssl-mode=%s without DB_SSL_CA: TLS is on but the server is not verified",
            mode,
        )
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _connect_args(database_url: str) -> dict:
    """Parse mysql:// or mysql+pymysql:// URLs into PyMySQL keyword arguments.

    A ?ssl-mode=REQUIRED|VERIFY_CA|VERIFY_IDENTITY query enables TLS."""
    url = urlparse(database_url)
    if url.scheme not in ("mysql", "mysql+pymysql"):
        raise ValueError(f"Unsupported database scheme: {url.scheme!r}")
    args = {
        "host": url.hostname or "localhost",
        "port": url.port or 3306,
        "user": unquote(url.username or ""),
        "password": unquote(url.password or ""),
        "database": unquote(url.path.lstrip("/")),
    }
    ctx = _ssl_context(_ssl_mode(url.query))
    if ctx is not None:
        args["ssl"] = ctx
    return args


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
