"""Responsibility: Define the role-named PlanningDispatcher collaborator contract for transports.
Public interface:
`-- PlanningDispatcher
    +-- advance_screen(session_id, target_screen)
    +-- cancel_session(session_id)
    +-- confirm_plan(session_id, confirmed)
    +-- execute_operations(session_id, original_words, operations, verdicts)
    +-- get_fetch_window(sources, vault_root)
    +-- get_session_state(session_id)
    `-- start_session(date, focus, messages, checked_sources, vault_root)
"""

from collections.abc import Mapping, Sequence
from typing import Protocol

from pydantic import JsonValue


class PlanningDispatcher(Protocol):
    """Dispatch planning session commands and return structured `tool-results.json` bodies."""

    async def start_session(
        self,
        date: str | None = None,
        focus: str | None = None,
        messages: Sequence[Mapping[str, JsonValue]] = (),
        checked_sources: Sequence[str] = (),
        vault_root: str | None = None,
    ) -> dict[str, JsonValue]:
        """Start a planning session for `vault_root` and return screen 1."""
        ...

    def get_fetch_window(
        self,
        sources: Sequence[str] = ("gmail", "slack"),
        vault_root: str | None = None,
    ) -> dict[str, JsonValue]:
        """Return per-source fetch windows for `vault_root` without starting a session."""
        ...

    def get_session_state(self, session_id: str) -> dict[str, JsonValue]:
        """Return the current screen of `session_id` without mutating it."""
        ...

    def execute_operations(
        self,
        session_id: str,
        original_words: str,
        operations: Sequence[Mapping[str, JsonValue]] = (),
        verdicts: Sequence[Mapping[str, JsonValue]] = (),
    ) -> dict[str, JsonValue]:
        """Apply explicit verdicts and operations to `session_id`."""
        ...

    def advance_screen(self, session_id: str, target_screen: int) -> dict[str, JsonValue]:
        """Advance `session_id` forward to `target_screen`."""
        ...

    def confirm_plan(self, session_id: str, confirmed: bool) -> dict[str, JsonValue]:
        """Confirm and persist `session_id` when `confirmed` is true."""
        ...

    def cancel_session(self, session_id: str) -> dict[str, JsonValue]:
        """Discard `session_id` without writing to disk."""
        ...
