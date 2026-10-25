class DomainError(Exception):
    """Business-rule failure. `code` matches the SIGNAL message of the stored procedures."""

    code: str = "DOMAIN_ERROR"
    default_message: str = "Domain error"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class TicketNotFound(DomainError):
    code = "TICKET_NOT_FOUND"
    default_message = "Ticket not found"


class OperatorNotFound(DomainError):
    code = "OPERATOR_NOT_FOUND"
    default_message = "Operator not found"


class ConcurrencyConflict(DomainError):
    code = "CONCURRENCY_CONFLICT"
    default_message = "The ticket was modified by someone else; reload and retry"


class InvalidTransition(DomainError):
    code = "INVALID_TRANSITION"
    default_message = "Transition not allowed"


class DiagnosisRequired(DomainError):
    code = "DIAGNOSIS_REQUIRED"
    default_message = "A diagnosis is required for this transition"


class CommentRequired(DomainError):
    code = "COMMENT_REQUIRED"
    default_message = "A comment is required for this transition"


class TicketClosed(DomainError):
    code = "TICKET_CLOSED"
    default_message = "The ticket is closed and can no longer be assigned"


class CommentEmpty(DomainError):
    code = "COMMENT_EMPTY"
    default_message = "Comment must not be empty"


CODE_TO_ERROR: dict[str, type[DomainError]] = {
    cls.code: cls
    for cls in (
        TicketNotFound,
        OperatorNotFound,
        ConcurrencyConflict,
        InvalidTransition,
        DiagnosisRequired,
        CommentRequired,
        CommentEmpty,
        TicketClosed,
    )
}
