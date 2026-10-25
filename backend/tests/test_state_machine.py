from itertools import product

import pytest

from app.domain.exceptions import (
    CommentRequired,
    DiagnosisRequired,
    InvalidTransition,
)
from app.domain.state_machine import TRANSITIONS, TransitionRule, allowed_from, validate_transition
from app.domain.status import TicketStatus as S

# (from, to, requires_diagnosis, requires_comment) - mirrors the spec / allowed_transition table.
SPEC_ROWS = {
    (S.PENDING, S.IN_PROGRESS, False, False),
    (S.PENDING, S.CANCELLED, False, True),
    (S.IN_PROGRESS, S.RESOLVED, True, False),
    (S.IN_PROGRESS, S.PENDING, False, True),
    (S.IN_PROGRESS, S.CANCELLED, False, True),
}
VALID = {(f, t): (d, c) for f, t, d, c in SPEC_ROWS}
ALL_PAIRS = list(product(S, S))


def test_transitions_match_spec_rows() -> None:
    actual = {
        (frm, r.to_status, r.requires_diagnosis, r.requires_comment)
        for frm, rules in TRANSITIONS.items()
        for r in rules
    }
    assert actual == SPEC_ROWS


def test_all_sixteen_pairs_covered() -> None:
    assert len(ALL_PAIRS) == 16


@pytest.mark.parametrize(("frm", "to"), ALL_PAIRS)
def test_every_pair(frm: S, to: S) -> None:
    if (frm, to) in VALID:
        needs_diag, needs_comment = VALID[(frm, to)]
        validate_transition(
            frm,
            to,
            diagnosis="found it" if needs_diag else None,
            comment="because" if needs_comment else None,
        )
    else:
        with pytest.raises(InvalidTransition):
            validate_transition(frm, to, diagnosis="d", comment="c")


@pytest.mark.parametrize("blank", [None, "", "   ", "\t\n"])
def test_blank_diagnosis_required(blank: str | None) -> None:
    with pytest.raises(DiagnosisRequired):
        validate_transition(S.IN_PROGRESS, S.RESOLVED, diagnosis=blank, comment=None)


@pytest.mark.parametrize("blank", [None, "", "   "])
def test_blank_comment_required(blank: str | None) -> None:
    with pytest.raises(CommentRequired):
        validate_transition(S.PENDING, S.CANCELLED, diagnosis=None, comment=blank)


def test_pending_to_resolved_is_invalid() -> None:
    with pytest.raises(InvalidTransition):
        validate_transition(S.PENDING, S.RESOLVED, diagnosis="d", comment="c")


@pytest.mark.parametrize("final", [S.RESOLVED, S.CANCELLED])
def test_final_states_have_no_transitions(final: S) -> None:
    assert allowed_from(final) == ()


def test_allowed_from_in_progress() -> None:
    targets = {r.to_status for r in allowed_from(S.IN_PROGRESS)}
    assert targets == {S.RESOLVED, S.PENDING, S.CANCELLED}
    assert all(isinstance(r, TransitionRule) for r in allowed_from(S.IN_PROGRESS))
