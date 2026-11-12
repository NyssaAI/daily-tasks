"""Responsibility: Orchestrate persisting a confirmed planning session across vault records and runtime state.
Public interface:
`-- SessionCommitterLocal
    +-- commit(changes, document, decisions, suggestions, session, cursors, confirmed_by_user)
    `-- new(file_store, decision_log_store, session_store, suggestions_repository, cursor_store)
"""

from collections.abc import Sequence
from typing import final

from nyssa_ai_result import Result, fail, ok

from daily_tasks.core.communications.cursor_store import CursorStore
from daily_tasks.core.communications.fetch_cursors import FetchCursors
from daily_tasks.core.communications.suggestions import Suggestions
from daily_tasks.core.communications.suggestions_repository import SuggestionsRepository
from daily_tasks.core.planning.decision_log_entry import DecisionLogEntry
from daily_tasks.core.planning.planning_session import PlanningSession
from daily_tasks.core.records.file_store import FileStore
from daily_tasks.core.records.record_change import RecordChange
from daily_tasks.core.records.types import DailyPlanDocument
from daily_tasks.planning.confirm_plan import ConfirmPlan
from daily_tasks.planning.decision_log_store_json import DecisionLogStoreJson
from daily_tasks.planning.decision_logger import DecisionLogger
from daily_tasks.planning.session_store_json import SessionStoreJson


@final
class SessionCommitterLocal:
    """Entity-first `SessionCommitter` coordinating vault record writes and runtime JSON state writes."""

    def __init__(
        self,
        file_store: FileStore,
        decision_log_store: DecisionLogStoreJson,
        session_store: SessionStoreJson,
        suggestions_repository: SuggestionsRepository,
        cursor_store: CursorStore | None = None,
    ) -> None:
        """Keep the vault `FileStore` and runtime persistence stores."""
        self._file_store = file_store
        self._decision_log_store = decision_log_store
        self._session_store = session_store
        self._suggestions_repository = suggestions_repository
        self._cursor_store = cursor_store

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
        """Apply `changes`, write `document`, and persist runtime logs, suggestions, session, and cursors."""
        written = ConfirmPlan(self._file_store).confirm(changes, document, confirmed_by_user)
        if not written.ok:
            return written
        appended = DecisionLogger(self._decision_log_store).append(decisions)
        if not appended.ok:
            return fail(appended.message, appended.category)
        steps = [
            self._suggestions_repository.save(suggestions),
            self._session_store.save_session(session),
        ]
        if self._cursor_store is not None and cursors is not None:
            steps.append(self._cursor_store.save(cursors))
        failed = next((step for step in steps if not step.ok), None)
        if failed is not None:
            return fail(failed.message, failed.category)
        return ok(written.value)
