# Responsibility: Group the plain values that read ports return.
# Public interface:
# +-- FetchBatch
# |   +-- cursors
# |   `-- messages
# +-- MalformedRecord
# |   +-- code
# |   +-- kind
# |   +-- message
# |   `-- path
# `-- ProjectPlanSnapshot
#     +-- blockers
#     +-- malformed_records
#     +-- milestones
#     +-- projects
#     `-- tasks
"""Read-port return values: a project plan snapshot, malformed records and one batch of fetched messages."""

from dataclasses import dataclass

from daily_tasks.domain import Blocker, FetchCursors, Message, Milestone, Project, Task


@dataclass(frozen=True, slots=True, kw_only=True)
class MalformedRecord:
    """A record file that failed to parse or validate during read."""

    path: str
    kind: str
    code: str
    message: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ProjectPlanSnapshot:
    """Every active project record one project plan source holds, read at one point in time."""

    projects: tuple[Project, ...]
    milestones: tuple[Milestone, ...]
    tasks: tuple[Task, ...]
    blockers: tuple[Blocker, ...]
    malformed_records: tuple[MalformedRecord, ...] = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class FetchBatch:
    """Messages newer than the cursors a fetch started from, and the advanced cursors."""

    messages: tuple[Message, ...]
    cursors: FetchCursors
