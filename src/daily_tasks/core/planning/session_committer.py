"""Responsibility: Define the role-named SessionCommitter collaborator contract.
Public interface:
`-- SessionCommitter
    `-- commit(changes, document, decisions, suggestions, session, cursors, confirmed_by_user)
"""

from collections.abc import Sequence
from typing import Protocol

from nyssa_ai_result import Result

from daily_tasks.core.communications.fetch_cursors import FetchCursors
from daily_tasks.core.communications.suggestions import Suggestions
from daily_tasks.core.planning.decision_log_entry import DecisionLogEntry
from daily_tasks.core.planning.planning_session import PlanningSession
from daily_tasks.core.records.record_change import RecordChange
from daily_tasks.core.records.types import DailyPlanDocument


class SessionCommitter(Protocol):
    """Persist a confirmed planning session across vault records and runtime state."""

    def commit(
        self,
        changes: Sequence[RecordChange],
        document: DailyPlanDocument,
        decisions: Sequence[DecisionLogEntry],
        suggestions: Suggestions,
        session: PlanningSession,
        cursors: FetchCursors | None,
        confirmed_by_user: bool,
    ) -> Result[str]:
        """Apply `changes`, write `document`, and persist runtime logs/suggestions/cursors."""
        ...
