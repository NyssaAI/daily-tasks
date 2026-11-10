"""Responsibility: Turn the host's row-numbered verdicts into adjudication verdicts on the current screen.
Public interface:
`-- parse_verdicts(session, verdicts, original_words)

Rows resolve against the current screen only; a bare row without accept/edit/reject is refused.
"""

from collections.abc import Mapping, Sequence
from typing import Literal

from nyssa_ai_result import ErrorCategory, Result, fail, ok
from pydantic import JsonValue

from daily_tasks.domain import PlanningSession
from daily_tasks.session.adjudication_verdict import AdjudicationVerdict
from daily_tasks.session.resolve_row import resolve_row

type _Verdict = Literal["accept", "edit", "reject"]
_VERDICTS: dict[JsonValue, _Verdict] = {"accept": "accept", "edit": "edit", "reject": "reject"}


def parse_verdicts(
    session: PlanningSession, verdicts: Sequence[Mapping[str, JsonValue]], original_words: str
) -> Result[tuple[AdjudicationVerdict, ...]]:
    """Return one verdict per `{"row", "verdict", "edits"?}` item.

    Fails with `invalid_verdict` or `not_a_suggestion` (Validation), or with `resolve_row`'s failure.
    """
    parsed: list[AdjudicationVerdict] = []
    for item in verdicts:
        row, verdict, edits = item.get("row"), _VERDICTS.get(item.get("verdict")), item.get("edits")
        if not isinstance(row, int) or isinstance(row, bool) or verdict is None:
            return fail("invalid_verdict: each verdict needs an integer row and accept/edit/reject.", "Validation")
        ref = resolve_row(session, str(row))
        if not ref.ok:
            return fail(ref.message, ref.category)
        if ref.value.kind != "suggestion":
            return fail(f"not_a_suggestion: row {row} is not a suggestion.", ErrorCategory.VALIDATION)
        parsed.append(
            AdjudicationVerdict(
                suggestion_id=ref.value.id,
                verdict=verdict,
                screen_id=session.current_screen,
                row=row,
                original_words=original_words,
                edits=edits if isinstance(edits, dict) else None,
            )
        )
    return ok(tuple(parsed))
