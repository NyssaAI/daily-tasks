"""Responsibility: Decide whether a work or blocker state is final.
Public interface:
`-- is_terminal_state(state)

Terminal states: completed or cancelled work, resolved blockers.
"""

from typing import Final

_TERMINAL: Final[frozenset[str]] = frozenset({"completed", "cancelled", "resolved"})


def is_terminal_state(state: str) -> bool:
    """Return True for `completed`, `cancelled` and `resolved`."""
    return state in _TERMINAL
