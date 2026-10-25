"""Safety guard for integration tests that DROP and recreate tables."""

from collections.abc import Mapping


class UnsafeTestDatabase(Exception):
    """TEST_DATABASE_URL points at the application database."""


def resolve_test_database_url(env: Mapping[str, str]) -> str | None:
    """Return TEST_DATABASE_URL, or None when unset. Never falls back to DATABASE_URL."""
    test_url = env.get("TEST_DATABASE_URL", "").strip()
    if not test_url:
        return None
    if test_url == env.get("DATABASE_URL", "").strip():
        raise UnsafeTestDatabase("TEST_DATABASE_URL must differ from DATABASE_URL; refusing to run")
    return test_url
