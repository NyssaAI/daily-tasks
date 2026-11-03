# Responsibility: Group the plain settings a state graph build needs beside the source records.
# Public interface:
# +-- DailyPlanSourceRead
# |   +-- error
# |   +-- name
# |   `-- plans
# +-- GraphRecords
# |   +-- blockers
# |   +-- milestones
# |   +-- plans
# |   +-- projects
# |   `-- tasks
# +-- ProjectPlanSourceRead
# |   +-- error
# |   +-- name
# |   `-- snapshot
# +-- RecordRelations
# |   +-- blocked_by
# |   +-- blocks
# |   +-- depends_on
# |   +-- diagnostics
# |   `-- required_by
# `-- StateGraphSettings
#     +-- changed_outside_app
#     +-- daily_plans_root
#     +-- file_hashes
#     +-- origin_by_record
#     +-- pending_operations
#     +-- projects_root
#     +-- threads
#     +-- timezone
#     +-- unreviewed_messages
#     +-- user
#     `-- workspace_root
"""Build settings, per-source read outcomes, the source records keyed by id, and the resolved relations between them."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from uuid import UUID

from daily_tasks.domain import Blocker, DailyPlan, Diagnostic, GraphUser, Milestone, Project, RecordOrigin, Task
from daily_tasks.ports import ProjectPlanSnapshot


@dataclass(frozen=True, slots=True, kw_only=True)
class StateGraphSettings:
    """Build inputs that do not come from the record sources.

    `file_hashes` maps workspace-relative record paths to content hashes; daily plan hashes are added
    from the plans themselves. The counts feed `derived.summary` unchanged.
    """

    workspace_root: str
    projects_root: str
    daily_plans_root: str
    user: GraphUser
    timezone: str
    file_hashes: Mapping[str, str] = field(default_factory=dict)
    threads: Mapping[str, tuple[UUID, ...]] = field(default_factory=dict)
    origin_by_record: Mapping[UUID, RecordOrigin] = field(default_factory=dict)
    pending_operations: int = 0
    unreviewed_messages: int = 0
    changed_outside_app: int = 0


@dataclass(frozen=True, slots=True, kw_only=True)
class GraphRecords:
    """Records of every source keyed by id (unique across kinds), and daily plans keyed by local date."""

    projects: Mapping[UUID, Project]
    milestones: Mapping[UUID, Milestone]
    tasks: Mapping[UUID, Task]
    blockers: Mapping[UUID, Blocker]
    plans: Mapping[date, DailyPlan]


@dataclass(frozen=True, slots=True, kw_only=True)
class RecordRelations:
    """Dependency and blocker relations in both directions; references to unknown ids become diagnostics."""

    depends_on: Mapping[UUID, tuple[UUID, ...]]
    required_by: Mapping[UUID, tuple[UUID, ...]]
    blocked_by: Mapping[UUID, tuple[UUID, ...]]
    blocks: Mapping[UUID, tuple[UUID, ...]]
    diagnostics: tuple[Diagnostic, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class ProjectPlanSourceRead:
    """Outcome of one project-plan source read: a snapshot, or the safe error message of a failed read."""

    name: str
    snapshot: ProjectPlanSnapshot | None
    error: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class DailyPlanSourceRead:
    """Outcome of one daily-plan source read: its plans, or the safe error message of a failed read."""

    name: str
    plans: tuple[DailyPlan, ...]
    error: str | None = None
