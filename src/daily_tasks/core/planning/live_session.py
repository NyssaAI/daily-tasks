"""Responsibility: Hold one in-memory planning session with what it read and what it staged.
Public interface:
`-- LiveSession
    +-- blockers
    +-- changes
    +-- cursors
    +-- decisions
    +-- existing_plan
    +-- malformed_files
    +-- previous_plan
    +-- state
    `-- suggestions
"""

from collections.abc import Mapping
from dataclasses import dataclass
from uuid import UUID

from daily_tasks.core.communications.fetch_cursors import FetchCursors
from daily_tasks.core.communications.suggestions import Suggestions
from daily_tasks.core.planning.decision_log_entry import DecisionLogEntry
from daily_tasks.core.planning.session_state import SessionState
from daily_tasks.core.records.blocker import Blocker
from daily_tasks.core.records.daily_plan import DailyPlan
from daily_tasks.core.records.record_change import RecordChange
from daily_tasks.core.records.types import MalformedRecord


@dataclass(frozen=True, slots=True, kw_only=True)
class LiveSession:
    """Session state plus staged decisions and record changes, in the order the user made them."""

    state: SessionState
    suggestions: Suggestions
    decisions: tuple[DecisionLogEntry, ...]
    changes: tuple[RecordChange, ...]
    blockers: Mapping[UUID, Blocker]
    existing_plan: DailyPlan | None
    previous_plan: DailyPlan | None
    cursors: FetchCursors | None
    malformed_files: tuple[MalformedRecord, ...] = ()
