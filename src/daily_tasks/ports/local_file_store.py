"""Responsibility: Define the only port allowed to write records, daily plans and planning state.
Public interface:
`-- LocalFileStore
    +-- append_decisions(entries)
    +-- apply(changes)
    +-- save_session(session)
    +-- save_suggestions(suggestions)
    `-- write_daily_plan(document)

Local File Store contract: validated writes, made only after explicit user adjudication.
"""

from collections.abc import Sequence
from typing import Protocol

from nyssa_ai_result import Result

from daily_tasks.domain import DecisionLogEntry, PlanningSession, RecordChange, Suggestions
from daily_tasks.storage.cst import DailyPlanDocument


class LocalFileStore(Protocol):
    """Writes Markdown records and `.nyssa-ai/daily-tasks/` state; callers pass only adjudicated changes."""

    def apply(self, changes: Sequence[RecordChange]) -> Result[tuple[RecordChange, ...]]:
        """Apply record changes atomically and return them marked applied.

        Fails with `Conflict` when a record's current hash differs from `expected_hash`; then no file
        is changed.
        """
        ...

    def write_daily_plan(self, document: DailyPlanDocument) -> Result[str]:
        """Write the daily plan Markdown atomically and return its path relative to the workspace."""
        ...

    def save_suggestions(self, suggestions: Suggestions) -> Result[None]:
        """Replace `suggestions.json` atomically."""
        ...

    def append_decisions(self, entries: Sequence[DecisionLogEntry]) -> Result[None]:
        """Append entries to `decision-log.json` atomically; existing entries are never rewritten."""
        ...

    def save_session(self, session: PlanningSession) -> Result[None]:
        """Replace the session record for the session's local date atomically."""
        ...
