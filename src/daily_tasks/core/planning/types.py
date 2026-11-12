"""Responsibility: Define immutable value objects for planning session orchestration.
Public interface:
+-- HarnessIntake
|   +-- cursors
|   +-- messages
|   `-- sources
+-- PlanningContext
|   +-- initial_lookback_days
|   +-- projects_prefix
|   +-- user_email
|   `-- vault_root
`-- VaultSnapshot
    +-- blockers
    +-- cursors
    +-- existing_plan
    +-- graph
    +-- malformed_files
    +-- messages
    +-- previous_plan
    `-- sources
"""

from collections.abc import Mapping
from dataclasses import dataclass
from uuid import UUID

from daily_tasks.core.communications.communication_message import CommunicationMessage
from daily_tasks.core.communications.fetch_cursors import FetchCursors
from daily_tasks.core.communications.message_source_status import MessageSourceStatus
from daily_tasks.core.records.blocker import Blocker
from daily_tasks.core.records.daily_plan import DailyPlan
from daily_tasks.core.records.state_graph import StateGraph
from daily_tasks.core.records.types import MalformedRecord


@dataclass(frozen=True, slots=True, kw_only=True)
class PlanningContext:
    """Resolved vault identity and lookback settings for one `PlanningTools` instance."""

    vault_root: str
    projects_prefix: str
    user_email: str
    initial_lookback_days: int = 7


@dataclass(frozen=True, slots=True, kw_only=True)
class VaultSnapshot:
    """In-memory snapshot of a vault's records, plans, and fetched communication messages."""

    graph: StateGraph
    blockers: Mapping[UUID, Blocker]
    existing_plan: DailyPlan | None
    previous_plan: DailyPlan | None
    messages: tuple[CommunicationMessage, ...]
    sources: tuple[MessageSourceStatus, ...] = ()
    cursors: FetchCursors | None = None
    malformed_files: tuple[MalformedRecord, ...] = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class HarnessIntake:
    """Validated host-provided messages merged with connector messages and advanced cursors."""

    messages: tuple[CommunicationMessage, ...]
    cursors: FetchCursors | None
    sources: tuple[str, ...] = ()
