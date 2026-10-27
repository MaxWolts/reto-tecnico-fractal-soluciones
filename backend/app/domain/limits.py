"""Accepted range for user-supplied dates; keeps date arithmetic and tz conversion overflow-free."""

from datetime import date, datetime

MIN_DATE = date(2000, 1, 1)
MAX_DATE = date(2099, 12, 31)


def check_date(value: date) -> date:
    if not MIN_DATE <= value <= MAX_DATE:
        raise ValueError(f"Date must be between {MIN_DATE} and {MAX_DATE}")
    return value


def check_datetime(value: datetime) -> datetime:
    # The wall-clock date is checked, so a UTC offset (at most 24h) cannot overflow.
    check_date(value.date())
    return value
