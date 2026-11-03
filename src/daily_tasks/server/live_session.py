# Responsibility: Hold one in-memory planning session with what it read and what it staged.
# Public interface:
# `-- LiveSession
#     +-- blockers
#     +-- changes
#     +-- cursors
#     +-- decisions
#     +-- existing_plan
#     +-- malformed_files
#     +-- previous_plan
#     +-- state
#     `-- suggestions
"""RAM-only session record; nothing in it reaches disk before the user confirms the plan."""

from collections.abc import Mapping
from dataclasses import dataclass
from uuid import UUID

from daily_tasks.domain import Blocker, DailyPlan, DecisionLogEntry, FetchCursors, RecordChange, Suggestions
from daily_tasks.ports import MalformedRecord
from daily_tasks.session import SessionState


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
