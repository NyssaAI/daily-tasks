# Responsibility: Group the in-memory state graph snapshot DTOs except derived facts.
# Public interface:
# +-- BlockerNode
# |   +-- owner
# |   +-- project_id
# |   +-- ref
# |   +-- state
# |   `-- title
# +-- GraphUser
# |   +-- email
# |   `-- name
# +-- MilestoneNode
# |   +-- number
# |   +-- project_id
# |   +-- ref
# |   +-- state
# |   `-- title
# +-- MilestoneTree
# |   +-- milestone_id
# |   `-- task_ids
# +-- PersonIndex
# |   +-- assigned
# |   `-- owns
# +-- PlanNode
# |   +-- completed_ids
# |   +-- path
# |   +-- ref
# |   `-- task_ids
# +-- ProjectNode
# |   +-- directory_date
# |   +-- owner
# |   +-- ref
# |   +-- state
# |   `-- title
# +-- ProjectTree
# |   +-- blocker_ids
# |   +-- milestones
# |   `-- project_id
# +-- RecordOrigin
# |   +-- decision_id
# |   +-- origin_kind
# |   `-- source_label
# +-- RecordSourceStatus
# |   +-- error
# |   +-- name
# |   +-- port
# |   +-- record_count
# |   `-- status
# +-- StateGraph
# |   +-- context
# |   +-- derived
# |   +-- diagnostics
# |   +-- index
# |   +-- note
# |   +-- records
# |   `-- tree
# +-- StateGraphContext
# |   +-- built_at
# |   +-- daily_plans_root
# |   +-- inventory_hash
# |   +-- local_date
# |   +-- projects_root
# |   +-- sources
# |   +-- timezone
# |   +-- user
# |   `-- workspace_root
# +-- StateGraphIndex
# |   +-- blocked_by
# |   +-- blocks
# |   +-- by_path
# |   +-- by_person
# |   +-- depends_on
# |   +-- file_hashes
# |   +-- origin_by_record
# |   +-- parent
# |   +-- project_order
# |   +-- required_by
# |   +-- threads
# |   `-- title_terms
# +-- StateGraphRecords
# |   +-- blockers
# |   +-- milestones
# |   +-- plans
# |   +-- projects
# |   `-- tasks
# `-- TaskNode
#     +-- assignee
#     +-- milestone_id
#     +-- owner
#     +-- ref
#     +-- state
#     +-- target_date
#     `-- title
"""StateGraph layers: context, records, tree, index and diagnostics."""

from collections.abc import Mapping
from datetime import date

from pydantic import MISSING, UUID7, Field
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.state_graph.derived.types import StateGraphDerived
from daily_tasks.domain.types import Diagnostic
from daily_tasks.domain.utc_timestamp import UtcTimestamp


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class GraphUser:
    """User the graph was built for."""

    name: str
    email: str


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class RecordSourceStatus:
    """Outcome of reading one project-plan or daily-plan source."""

    port: str
    name: str
    status: str
    record_count: int
    error: str | None


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class StateGraphContext:
    """Roots, user, day and inventory hash the graph was built from."""

    workspace_root: str
    projects_root: str
    daily_plans_root: str
    user: GraphUser
    timezone: str
    local_date: date
    built_at: UtcTimestamp
    inventory_hash: str
    sources: tuple[RecordSourceStatus, ...]


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class ProjectNode:
    """Project fields the graph keeps in memory."""

    ref: str | MISSING = Field(default=MISSING, alias="$ref")
    title: str
    state: str
    owner: str | MISSING = MISSING
    directory_date: date


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MilestoneNode:
    """Milestone fields the graph keeps in memory."""

    ref: str | MISSING = Field(default=MISSING, alias="$ref")
    project_id: UUID7
    number: int
    title: str
    state: str


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class TaskNode:
    """Task fields the graph keeps in memory."""

    ref: str | MISSING = Field(default=MISSING, alias="$ref")
    milestone_id: UUID7
    title: str
    state: str
    owner: str
    assignee: str | None
    target_date: date | None


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class BlockerNode:
    """Blocker fields the graph keeps in memory."""

    ref: str | MISSING = Field(default=MISSING, alias="$ref")
    project_id: UUID7
    title: str
    state: str
    owner: str


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class PlanNode:
    """Daily plan fields the graph keeps in memory."""

    ref: str | MISSING = Field(default=MISSING, alias="$ref")
    path: str | MISSING = MISSING
    task_ids: tuple[UUID7, ...]
    completed_ids: tuple[UUID7, ...] | MISSING = MISSING


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class StateGraphRecords:
    """Flat records by id, and daily plans by local date."""

    projects: Mapping[UUID7, ProjectNode]
    milestones: Mapping[UUID7, MilestoneNode]
    tasks: Mapping[UUID7, TaskNode]
    blockers: Mapping[UUID7, BlockerNode]
    plans: Mapping[date, PlanNode]


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MilestoneTree:
    """Milestone and its task ids in order."""

    milestone_id: UUID7
    task_ids: tuple[UUID7, ...]


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class ProjectTree:
    """Project with its nested milestones and blockers."""

    project_id: UUID7
    milestones: tuple[MilestoneTree, ...]
    blocker_ids: tuple[UUID7, ...]


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class PersonIndex:
    """Records a person owns and is assigned."""

    owns: tuple[UUID7, ...]
    assigned: tuple[UUID7, ...]


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class RecordOrigin:
    """How a record came to exist, for records created from a decision."""

    origin_kind: str
    source_label: str
    decision_id: UUID7


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class StateGraphIndex:
    """Relations and lookups between records."""

    project_order: tuple[UUID7, ...]
    parent: Mapping[UUID7, UUID7]
    depends_on: Mapping[UUID7, tuple[UUID7, ...]]
    required_by: Mapping[UUID7, tuple[UUID7, ...]]
    blocked_by: Mapping[UUID7, tuple[UUID7, ...]]
    blocks: Mapping[UUID7, tuple[UUID7, ...]]
    by_path: Mapping[str, UUID7]
    by_person: Mapping[str, PersonIndex]
    origin_by_record: Mapping[UUID7, RecordOrigin]
    title_terms: Mapping[str, tuple[UUID7, ...]]
    threads: Mapping[str, tuple[UUID7, ...]]
    file_hashes: Mapping[str, str]


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class StateGraph:
    """Point-in-time state graph, rebuilt from the configured record sources."""

    note: str | MISSING = Field(default=MISSING, alias="_note")
    context: StateGraphContext
    records: StateGraphRecords
    tree: tuple[ProjectTree, ...]
    index: StateGraphIndex
    derived: StateGraphDerived
    diagnostics: tuple[Diagnostic, ...]
