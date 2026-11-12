"""Responsibility: Group immutable data structures shared across record repositories and state graphs.
Public interface:
+-- DailyPlanDocument
|   +-- blockers
|   +-- items
|   +-- maturity
|   +-- owner
|   +-- plan
|   +-- record_version
|   `-- tags
+-- DailyPlanRead
|   +-- error
|   +-- name
|   `-- plans
+-- GraphRecords
|   +-- blockers
|   +-- milestones
|   +-- plans
|   +-- projects
|   `-- tasks
+-- MalformedRecord
|   +-- code
|   +-- kind
|   +-- message
|   `-- path
+-- MilestoneState
+-- PlanBlockerView
|   +-- blocker_id
|   +-- impact
|   +-- owner
|   +-- path
|   +-- resolved_when
|   `-- title
+-- PlanItemView
|   +-- due_date
|   +-- item_id
|   +-- milestone_title
|   +-- path
|   +-- project_title
|   +-- status_mark
|   `-- title
+-- ProjectPlanRead
|   +-- error
|   +-- name
|   `-- snapshot
+-- ProjectPlanSnapshot
|   +-- blockers
|   +-- malformed_records
|   +-- milestones
|   +-- projects
|   `-- tasks
+-- ProjectState
+-- RecordLocation
|   +-- inherited_owner
|   +-- path
|   `-- source
+-- RecordRelations
|   +-- blocked_by
|   +-- blocks
|   +-- depends_on
|   +-- diagnostics
|   `-- required_by
+-- StateGraphSettings
|   +-- changed_outside_app
|   +-- daily_plans_root
|   +-- file_hashes
|   +-- origin_by_record
|   +-- pending_operations
|   +-- projects_root
|   +-- threads
|   +-- timezone
|   +-- unreviewed_messages
|   +-- user
|   `-- vault_root
`-- TaskState
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from uuid import UUID

from daily_tasks.core.records.blocker import Blocker
from daily_tasks.core.records.daily_plan import DailyPlan
from daily_tasks.core.records.diagnostic import Diagnostic
from daily_tasks.core.records.graph_user import GraphUser
from daily_tasks.core.records.milestone import Milestone
from daily_tasks.core.records.project import Project
from daily_tasks.core.records.record_kind import RecordKind
from daily_tasks.core.records.record_origin import RecordOrigin
from daily_tasks.core.records.task import Task
from daily_tasks.core.records.work_state import WorkState

type ProjectState = WorkState
type MilestoneState = WorkState
type TaskState = WorkState


@dataclass(frozen=True, slots=True, kw_only=True)
class MalformedRecord:
    """Skipped malformed or unreadable Markdown record surfaced as a scoped diagnostic."""

    path: str
    kind: RecordKind
    code: str
    message: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ProjectPlanSnapshot:
    """Point-in-time snapshot of records read from one project-plan repository."""

    projects: tuple[Project, ...]
    milestones: tuple[Milestone, ...]
    tasks: tuple[Task, ...]
    blockers: tuple[Blocker, ...]
    malformed_records: tuple[MalformedRecord, ...] = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class StateGraphSettings:
    """Build inputs that accompany source records during state graph compilation."""

    vault_root: str
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
    """Records of every repository keyed by UUID, and daily plans keyed by local date."""

    projects: Mapping[UUID, Project]
    milestones: Mapping[UUID, Milestone]
    tasks: Mapping[UUID, Task]
    blockers: Mapping[UUID, Blocker]
    plans: Mapping[date, DailyPlan]


@dataclass(frozen=True, slots=True, kw_only=True)
class RecordRelations:
    """Bidirectional dependency and blocker relations with unresolved-reference diagnostics."""

    depends_on: Mapping[UUID, tuple[UUID, ...]]
    required_by: Mapping[UUID, tuple[UUID, ...]]
    blocked_by: Mapping[UUID, tuple[UUID, ...]]
    blocks: Mapping[UUID, tuple[UUID, ...]]
    diagnostics: tuple[Diagnostic, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class ProjectPlanRead:
    """Outcome of one project-plan repository read."""

    name: str
    snapshot: ProjectPlanSnapshot | None
    error: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class DailyPlanRead:
    """Outcome of one daily-plan repository read."""

    name: str
    plans: tuple[DailyPlan, ...]
    error: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class RecordLocation:
    """Location metadata of a parsed record, including optional inherited owner."""

    path: str
    source: str
    inherited_owner: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class PlanItemView:
    """Rendered display row values for one task or blocker selected on a daily plan."""

    item_id: str
    title: str
    path: str
    project_title: str
    milestone_title: str | None
    status_mark: str
    due_date: date | None


@dataclass(frozen=True, slots=True, kw_only=True)
class PlanBlockerView:
    """Rendered display row values for one blocker under active resolution on a daily plan."""

    blocker_id: str
    title: str
    path: str
    impact: str
    owner: str
    resolved_when: str


@dataclass(frozen=True, slots=True, kw_only=True)
class DailyPlanDocument:
    """DailyPlan record paired with the display views and frontmatter needed to render Markdown."""

    plan: DailyPlan
    owner: str
    tags: tuple[str, ...]
    maturity: str
    record_version: int
    items: tuple[PlanItemView, ...]
    blockers: tuple[PlanBlockerView, ...]
