"""Infrastructure-level errors (not business rules; those live in app.domain.exceptions)."""


class DatabaseUnavailable(Exception):
    """The database cannot be reached or the connection was lost."""


class DataRejected(Exception):
    """The database rejected the data (CHECK violation or value too long)."""
