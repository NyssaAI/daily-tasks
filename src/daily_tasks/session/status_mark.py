# Responsibility: Map a record state to its legend mark on planning screens.
# Public interface:
# `-- status_mark(state)
"""Legend: [ ] not started/open · [>] in progress · [x] completed/resolved · [-] cancelled."""

from typing import Final

_MARKS: Final[dict[str, str]] = {
    "not-started": "[ ]",
    "open": "[ ]",
    "in-progress": "[>]",
    "completed": "[x]",
    "resolved": "[x]",
    "cancelled": "[-]",
}


def status_mark(state: str) -> str:
    """Return the legend mark for `state`; unknown states render as the raw value."""
    return _MARKS.get(state, state)
