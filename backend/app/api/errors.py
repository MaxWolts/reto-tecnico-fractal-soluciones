"""RFC 7807 problem+json handlers."""

import logging
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.domain.exceptions import (
    CommentEmpty,
    CommentRequired,
    ConcurrencyConflict,
    DiagnosisRequired,
    DomainError,
    InvalidTransition,
    OperatorNotFound,
    TicketClosed,
    TicketNotFound,
)
from app.errors import DatabaseUnavailable, DataRejected

logger = logging.getLogger(__name__)

PROBLEM_JSON = "application/problem+json"

STATUS_BY_CODE: dict[str, int] = {
    TicketNotFound.code: 404,
    OperatorNotFound.code: 404,
    ConcurrencyConflict.code: 409,
    InvalidTransition.code: 422,
    DiagnosisRequired.code: 422,
    CommentRequired.code: 422,
    CommentEmpty.code: 422,
    TicketClosed.code: 422,
}


def problem(status: int, code: str, detail: str, errors: list[dict] | None = None):
    body: dict = {
        "type": "about:blank",
        "title": HTTPStatus(status).phrase,
        "status": status,
        "detail": detail,
        "code": code,
    }
    if errors:
        body["errors"] = errors
    return JSONResponse(body, status_code=status, media_type=PROBLEM_JSON)


def _field(loc: tuple) -> str:
    parts = [str(p) for p in loc if p not in ("body", "query", "path")]
    return ".".join(parts)


async def domain_error_handler(_: Request, exc: DomainError):
    return problem(STATUS_BY_CODE.get(exc.code, 422), exc.code, exc.message)


async def validation_error_handler(_: Request, exc: RequestValidationError):
    errors = [{"field": _field(e["loc"]), "message": e["msg"]} for e in exc.errors()]
    return problem(400, "VALIDATION_ERROR", "Request validation failed", errors)


async def data_rejected_handler(_: Request, exc: DataRejected):
    return problem(400, "VALIDATION_ERROR", "The database rejected the submitted data")


async def database_unavailable_handler(_: Request, exc: DatabaseUnavailable):
    logger.error("Database unavailable: %s", exc)
    return problem(503, "DATABASE_UNAVAILABLE", "The database is currently unavailable")


async def http_exception_handler(_: Request, exc: StarletteHTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else HTTPStatus(exc.status_code).phrase
    response = problem(exc.status_code, f"HTTP_{exc.status_code}", detail)
    response.headers.update(exc.headers or {})
    return response


async def unhandled_error_handler(_: Request, exc: Exception):
    logger.exception("Unhandled error", exc_info=exc)
    return problem(500, "INTERNAL_ERROR", "An unexpected error occurred")


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, domain_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(DataRejected, data_rejected_handler)
    app.add_exception_handler(DatabaseUnavailable, database_unavailable_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
