# Responsibility: Group the plain settings and read snapshots the MCP server works with.
# Public interface:
# +-- HarnessIntake
# |   +-- cursors
# |   +-- messages
# |   `-- sources
# +-- ServerSettings
# |   +-- daily_plans_root
# |   +-- initial_lookback_days
# |   +-- projects_root
# |   +-- state_root
# |   +-- timezone
# |   +-- user
# |   `-- workspace_root
# `-- WorkspaceSnapshot
#     +-- blockers
#     +-- cursors
#     +-- existing_plan
#     +-- graph
#     +-- malformed_files
#     +-- messages
#     +-- previous_plan
#     `-- sources
"""Resolved absolute roots, the planning user, and what one session start read from the workspace."""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from daily_tasks.domain import Blocker, DailyPlan, FetchCursors, GraphUser, Message, MessageSourceStatus, StateGraph
from daily_tasks.ports import MalformedRecord


@dataclass(frozen=True, slots=True, kw_only=True)
class HarnessIntake:
    """Adapter and new harness messages together, the merged advanced cursors and the harness source names.

    `cursors` is None only when neither a connector nor the harness supplied anything to advance.
    """

    messages: tuple[Message, ...]
    cursors: FetchCursors | None
    sources: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class ServerSettings:
    """Absolute roots, never resolved against the working directory, plus the user and IANA timezone.

    `initial_lookback_days` bounds a source's first pull when it has no saved fetch cursor.
    """

    workspace_root: Path
    projects_root: Path
    daily_plans_root: Path
    state_root: Path
    user: GraphUser
    timezone: str
    initial_lookback_days: int = 7


@dataclass(frozen=True, slots=True, kw_only=True)
class WorkspaceSnapshot:
    """State graph plus the full blocker records, today's and the previous plan, and unread messages.

    `cursors` are the advanced fetch cursors, saved only when the plan is confirmed.
    """

    graph: StateGraph
    blockers: Mapping[UUID, Blocker]
    existing_plan: DailyPlan | None
    previous_plan: DailyPlan | None
    messages: tuple[Message, ...]
    cursors: FetchCursors | None
    sources: tuple[MessageSourceStatus, ...]
    malformed_files: tuple[MalformedRecord, ...] = ()
