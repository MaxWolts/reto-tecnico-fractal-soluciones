"""Create the database schema, stored procedures and demo data.

Usage (run from backend/):

    python scripts/init_db.py [--no-seed]

Reads DATABASE_URL from the environment, or from backend/.env when the
variable is not set. Accepted forms:

    mysql://user:password@host:3306/dbname
    mysql+pymysql://user:password@host:3306/dbname

Applies, in order:

    database/01_schema.sql             (DROPS AND RECREATES ALL TABLES)
    database/02_stored_procedures.sql
    database/03_seed.sql               (skipped with --no-seed)

When the database does not exist, it is created first.
Dependencies: Python standard library and PyMySQL only.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pymysql

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BACKEND_DIR.parent
DATABASE_DIR = REPO_DIR / "database"
ENV_FILE = BACKEND_DIR / ".env"

SCHEMA_FILE = DATABASE_DIR / "01_schema.sql"
PROCEDURES_FILE = DATABASE_DIR / "02_stored_procedures.sql"
SEED_FILE = DATABASE_DIR / "03_seed.sql"

ER_BAD_DB_ERROR = 1049

_DELIMITER_RE = re.compile(r"DELIMITER[ \t]+(\S+)[ \t]*(?:\r?\n|$)", re.IGNORECASE)


class InitDbError(Exception):
    """Raised with a user-facing message when initialization fails."""


# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
def _read_env_file(path: Path) -> dict[str, str]:
    """Parse simple KEY=VALUE lines. Ignores blanks, comments and `export `."""
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export ") :].lstrip()
        key, _, value = line.partition("=")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return values


def load_database_url(env_file: Path = ENV_FILE) -> str | None:
    """Return DATABASE_URL from the environment, else from env_file, else None."""
    url = os.environ.get("DATABASE_URL", "").strip()
    if url:
        return url
    return _read_env_file(env_file).get("DATABASE_URL", "").strip() or None


def parse_database_url(url: str) -> dict[str, object]:
    """Convert a mysql:// or mysql+pymysql:// URL into pymysql.connect kwargs."""
    parts = urlsplit(url)
    if parts.scheme not in ("mysql", "mysql+pymysql"):
        raise InitDbError(
            f"DATABASE_URL scheme must be mysql:// or mysql+pymysql://, got {parts.scheme!r}"
        )
    database = unquote(parts.path.lstrip("/"))
    if not parts.hostname or not database:
        raise InitDbError("DATABASE_URL must include a host and a database name")
    try:
        port = parts.port or 3306
    except ValueError as exc:
        raise InitDbError(f"DATABASE_URL has an invalid port: {exc}") from exc
    return {
        "host": parts.hostname,
        "port": port,
        "user": unquote(parts.username or ""),
        "password": unquote(parts.password or ""),
        "database": database,
    }


# --------------------------------------------------------------------------- #
# SQL splitting
# --------------------------------------------------------------------------- #
def split_sql(script: str) -> Iterator[str]:
    """Yield the statements of a MySQL script, like the mysql command-line client.

    - Honors `DELIMITER <token>` lines (the directive itself is not yielded).
    - Ignores delimiters inside '...', "..." and `...` (with backslash escapes
      and doubled quotes), and inside -- / # / C-style comments.
    - Comments outside strings are removed from the yielded statements.
    """
    delimiter = ";"
    buf: list[str] = []
    i = 0
    n = len(script)
    at_line_start = True

    def flush() -> str | None:
        statement = "".join(buf).strip()
        buf.clear()
        return statement or None

    while i < n:
        if at_line_start:
            # A DELIMITER directive must start a line (leading spaces allowed).
            j = i
            while j < n and script[j] in " \t":
                j += 1
            match = _DELIMITER_RE.match(script, j)
            if match:
                statement = flush()
                if statement:
                    yield statement
                delimiter = match.group(1)
                i = match.end()
                continue
        at_line_start = False

        ch = script[i]

        if script.startswith(delimiter, i):
            statement = flush()
            if statement:
                yield statement
            i += len(delimiter)
            continue

        if ch in "'\"`":
            end = _skip_quoted(script, i)
            buf.append(script[i:end])
            i = end
            continue

        if ch == "#" or (script.startswith("--", i) and (i + 2 >= n or script[i + 2] in " \t\r\n")):
            newline = script.find("\n", i)
            i = n if newline == -1 else newline
            continue

        if script.startswith("/*", i):
            close = script.find("*/", i + 2)
            if close == -1:
                raise InitDbError("Unterminated /* comment in SQL script")
            buf.append(" ")
            i = close + 2
            continue

        buf.append(ch)
        if ch == "\n":
            at_line_start = True
        i += 1

    statement = flush()
    if statement:
        yield statement


def _skip_quoted(script: str, start: int) -> int:
    """Return the index just after the quoted token that begins at start."""
    quote = script[start]
    i = start + 1
    n = len(script)
    while i < n:
        ch = script[i]
        if ch == "\\" and quote != "`":
            i += 2
            continue
        if ch == quote:
            if i + 1 < n and script[i + 1] == quote:  # doubled quote escape
                i += 2
                continue
            return i + 1
        i += 1
    raise InitDbError(f"Unterminated {quote} quote in SQL script")


# --------------------------------------------------------------------------- #
# Execution
# --------------------------------------------------------------------------- #
def connect(params: dict[str, object]) -> pymysql.connections.Connection:
    """Connect to the database, creating it first when it does not exist."""
    common = {"charset": "utf8mb4", "autocommit": True, "connect_timeout": 10}
    try:
        return pymysql.connect(**params, **common)
    except pymysql.err.OperationalError as exc:
        if exc.args[0] != ER_BAD_DB_ERROR:
            raise
    database = str(params["database"]).replace("`", "``")
    server_params = {k: v for k, v in params.items() if k != "database"}
    with pymysql.connect(**server_params, **common) as server:
        with server.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{database}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
    return pymysql.connect(**params, **common)


def apply_file(conn: pymysql.connections.Connection, path: Path) -> int:
    """Run every statement of a SQL file. Return the number of statements."""
    try:
        script = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise InitDbError(f"Cannot read {path}: {exc}") from exc
    count = 0
    with conn.cursor() as cur:
        for statement in split_sql(script):
            try:
                cur.execute(statement)
                while cur.nextset():
                    pass
            except pymysql.MySQLError as exc:
                preview = " ".join(statement.split())[:120]
                raise InitDbError(
                    f"{path.name}: statement {count + 1} failed: {exc}\n  SQL: {preview}"
                ) from exc
            count += 1
    return count


def init_db(url: str | None = None, seed: bool = True, verbose: bool = True) -> None:
    """Recreate schema and procedures, and load demo data when seed is True."""
    url = url or load_database_url()
    if not url:
        raise InitDbError(f"DATABASE_URL is not set (environment or {ENV_FILE})")
    params = parse_database_url(url)
    files = [SCHEMA_FILE, PROCEDURES_FILE] + ([SEED_FILE] if seed else [])
    try:
        conn = connect(params)
    except pymysql.MySQLError as exc:
        raise InitDbError(
            f"Cannot connect to MySQL at {params['host']}:{params['port']}: {exc}"
        ) from exc
    with conn:
        with conn.cursor() as cur:
            cur.execute("SET time_zone = '+00:00'")
        for path in files:
            count = apply_file(conn, path)
            if verbose:
                print(f"{path.name}: {count} statements")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Initialize the MySQL database.")
    parser.add_argument("--no-seed", action="store_true", help="skip 03_seed.sql")
    args = parser.parse_args(argv)
    try:
        init_db(seed=not args.no_seed)
    except InitDbError as exc:
        print(f"init_db failed: {exc}", file=sys.stderr)
        return 1
    print("Database ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
