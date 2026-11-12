"""Responsibility: Build small, valid project and daily plan records for state graph tests.
Public interface:
+-- BUILT_AT
+-- SETTINGS
+-- USER
+-- blocker(number, title, blocks, project_id, state, owner)
+-- milestone(number, title, state, project_id, done)
+-- plan(local_date, entries)
+-- project(number, title, directory_date, state)
+-- record_id(number)
`-- task(number, milestone_id, title, state, owner, assignee, target_date, done, depends_on, blocked_by)

Record factories with readable defaults; ids are UUIDv7 values numbered by `record_id`.
"""

from collections.abc import Sequence
from datetime import UTC, date, datetime
from typing import Final
from uuid import UUID

from daily_tasks.core.records import (
    Blocker,
    BlockerState,
    DailyPlan,
    DailyPlanEntry,
    DailyPlanSummary,
    DodItem,
    GraphUser,
    Milestone,
    Project,
    StateGraphSettings,
    Task,
    WorkState,
)

USER: Final[str] = "jordan@example.com"
BUILT_AT: Final[datetime] = datetime(2026, 11, 3, 14, 2, 3, tzinfo=UTC)
SETTINGS: Final[StateGraphSettings] = StateGraphSettings(
    vault_root="/vault",
    projects_root="/vault/1-projects",
    daily_plans_root="/vault/2-areas/daily-plans",
    user=GraphUser(name="Jordan", email=USER),
    timezone="America/Chicago",
)
_STAMP: Final[datetime] = datetime(2026, 10, 20, 14, 0, tzinfo=UTC)


def record_id(number: int) -> UUID:
    """Return a stable UUIDv7 for `number`."""
    return UUID(f"019a4b2c-1f00-7a10-8000-{number:012x}")


def project(
    number: int, title: str, directory_date: date = date(2026, 10, 20), state: WorkState = "in-progress"
) -> Project:
    """Return a project record."""
    return Project(
        id=record_id(number), type="project", title=title, description="", directory_date=directory_date,
        owner=USER, assignee=None, state=state, created_at=_STAMP, updated_at=_STAMP, started_at=None,
        resolved_at=None, target_date=None, tags=(), path=f"p{number}/project-index.md", milestone_ids=(),
        blocker_ids=(), source="markdown-projects",
    )  # fmt: skip


def milestone(
    number: int, title: str, state: WorkState = "in-progress", project_id: int = 1, done: Sequence[bool] = ()
) -> Milestone:
    """Return milestone `number` of project `project_id`; `done` lists its DoD item marks."""
    return Milestone(
        id=record_id(number), type="milestone", record_version=2, project_id=record_id(project_id), number=number,
        title=title, owner=USER, assignee=USER, state=state, created_at=_STAMP, updated_at=_STAMP, started_at=None,
        resolved_at=None, target_date=None, tags=(), path=f"p{project_id}/m{number}.md",
        definition_of_done=_dod(number, done), task_ids=(), blocked_by=(), source="markdown-projects",
    )  # fmt: skip


def task(
    number: int,
    milestone_id: int,
    title: str,
    state: WorkState = "not-started",
    owner: str = USER,
    assignee: str | None = None,
    target_date: date | None = None,
    done: Sequence[bool] = (False,),
    depends_on: Sequence[int] = (),
    blocked_by: Sequence[int] = (),
) -> Task:
    """Return a task of milestone `milestone_id` in project 1."""
    return Task(
        id=record_id(number), type="task", record_version=2, project_id=record_id(1),
        milestone_id=record_id(milestone_id), number=number, title=title, owner=owner, assignee=assignee,
        state=state, created_at=_STAMP, updated_at=_STAMP, started_at=None, resolved_at=None,
        target_date=target_date, tags=(), path=f"p1/m{milestone_id}/t{number}.md",
        definition_of_done=_dod(number, done), depends_on=tuple(record_id(n) for n in depends_on), required_by=(),
        blocked_by=tuple(record_id(n) for n in blocked_by), source="markdown-projects",
    )  # fmt: skip


def blocker(
    number: int,
    title: str,
    blocks: Sequence[int] = (),
    project_id: int = 1,
    state: BlockerState = "open",
    owner: str = USER,
) -> Blocker:
    """Return a blocker of project `project_id` that blocks the records numbered in `blocks`."""
    return Blocker(
        id=record_id(number), type="blocker", project_id=record_id(project_id), number=number, title=title,
        impact="", resolved_when="", owner=owner, state=state,
        created_at=_STAMP, updated_at=_STAMP, resolved_at=None, path=f"p{project_id}/blockers/b{number}.md",
        blocks=tuple(record_id(n) for n in blocks), source="markdown-projects",
    )  # fmt: skip


def plan(local_date: date, entries: Sequence[DailyPlanEntry]) -> DailyPlan:
    """Return the daily plan for `local_date` with `entries`."""
    return DailyPlan(
        id=record_id(0xD000 + local_date.toordinal() % 0x1000), type="daily-plan", local_date=local_date,
        timezone="America/Chicago", path=f"2-areas/daily-plans/{local_date:%Y.%m.%d}-daily-plan.md", created_at=_STAMP,
        updated_at=_STAMP, content_hash=f"sha256:{local_date:%Y%m%d}", focus=None,
        summary=DailyPlanSummary(open_projects=0, open_tasks=0, late_tasks=0), entries=tuple(entries),
        removed_item_ids=(), blockers=(), decisions=(), notes=(), source="markdown-daily-plans",
    )  # fmt: skip


def _dod(number: int, done: Sequence[bool]) -> tuple[DodItem, ...]:
    return tuple(
        DodItem(id=record_id(0x10000 * (index + 1) + number), text=f"item {index}", done=mark)
        for index, mark in enumerate(done)
    )
