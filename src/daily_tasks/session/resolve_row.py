# Responsibility: Resolve a reply's row number or milestone label against the current screen only.
# Public interface:
# `-- resolve_row(session, reference)
"""Numbers from another screen are refused; labels M1, M2… resolve within `current_project_id` on screen 2."""

from collections.abc import Mapping

from nyssa_ai_result import ErrorCategory, Result, fail, ok

from daily_tasks.domain import PlanningSession, RowRef


def _resolve_label(session: PlanningSession, label: str) -> Result[RowRef]:
    project_id = session.assign_days.current_project_id
    if not session.current_screen.startswith("s2:") or project_id is None:
        return fail(f"Milestone label {label} only applies on a project screen.", ErrorCategory.VALIDATION)
    milestone_id = session.labels.get(project_id, {}).get(label)
    if milestone_id is None:
        return fail(f"Milestone {label} is not on this project.", ErrorCategory.NOT_FOUND)
    return ok(RowRef(kind="milestone", id=milestone_id))


def resolve_row(session: PlanningSession, reference: str) -> Result[RowRef]:
    """Return the item `reference` ("12", "#12" or "M2") points at on `current_screen`.

    Fails with Validation for malformed references or when no screen is shown, NotFound for unknown labels,
    and Conflict for a number that is not on the current screen (including numbers from other screens).
    """
    text = reference.strip().removeprefix("#")
    if text[:1].upper() == "M" and text[1:].isdigit():
        return _resolve_label(session, "M" + text[1:])
    if not text.isdigit():
        return fail(f"'{reference}' is not a row number.", ErrorCategory.VALIDATION)
    screen = session.screens.get(session.current_screen)
    if screen is None:
        return fail("No screen is shown yet.", ErrorCategory.VALIDATION)
    rows = screen.rows if isinstance(screen.rows, Mapping) else {}
    number = int(text)
    ref = rows.get(number)
    if ref is None:
        return fail(
            f"Row {number} is not on the current screen; reply with a number shown on this screen.",
            ErrorCategory.CONFLICT,
        )
    return ok(ref)
