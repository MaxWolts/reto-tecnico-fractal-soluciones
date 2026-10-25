"""Ticket state machine.

TRANSITIONS mirrors the DB table `allowed_transition`; the stored procedure
`sp_change_ticket_status` re-validates under a row lock, so keep both in sync.
"""

from dataclasses import dataclass

from app.domain.exceptions import CommentRequired, DiagnosisRequired, InvalidTransition
from app.domain.status import TicketStatus as S


@dataclass(frozen=True)
class TransitionRule:
    to_status: S
    requires_diagnosis: bool = False
    requires_comment: bool = False


TRANSITIONS: dict[S, tuple[TransitionRule, ...]] = {
    S.PENDING: (
        TransitionRule(S.IN_PROGRESS),
        TransitionRule(S.CANCELLED, requires_comment=True),
    ),
    S.IN_PROGRESS: (
        TransitionRule(S.RESOLVED, requires_diagnosis=True),
        TransitionRule(S.PENDING, requires_comment=True),
        TransitionRule(S.CANCELLED, requires_comment=True),
    ),
    S.RESOLVED: (),
    S.CANCELLED: (),
}


def allowed_from(status: S) -> tuple[TransitionRule, ...]:
    return TRANSITIONS[status]


def _is_blank(value: str | None) -> bool:
    return value is None or not value.strip()


def validate_transition(
    from_status: S, to_status: S, diagnosis: str | None, comment: str | None
) -> TransitionRule:
    rule = next((r for r in allowed_from(from_status) if r.to_status == to_status), None)
    if rule is None:
        raise InvalidTransition(f"Cannot move from {from_status} to {to_status}")
    if rule.requires_diagnosis and _is_blank(diagnosis):
        raise DiagnosisRequired()
    if rule.requires_comment and _is_blank(comment):
        raise CommentRequired()
    return rule
