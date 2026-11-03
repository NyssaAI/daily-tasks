# Responsibility: Group the plain inputs that record parsing and plan rendering need beside the Markdown.
# Public interface:
# +-- DailyPlanDocument
# |   +-- blockers
# |   +-- items
# |   +-- maturity
# |   +-- owner
# |   +-- plan
# |   +-- record_version
# |   `-- tags
# +-- PlanBlockerView
# |   +-- blocker_id
# |   +-- impact
# |   +-- owner
# |   +-- path
# |   +-- resolved_when
# |   `-- title
# +-- PlanItemView
# |   +-- due_date
# |   +-- item_id
# |   +-- milestone_title
# |   +-- path
# |   +-- project_title
# |   +-- status_mark
# |   `-- title
# `-- RecordLocation
#     +-- inherited_owner
#     +-- path
#     `-- source
"""Record location and the display values of tasks and blockers listed in a daily plan."""

from dataclasses import dataclass
from datetime import date

from daily_tasks.domain import DailyPlan


@dataclass(frozen=True, slots=True, kw_only=True)
class RecordLocation:
    """Where a record was read from; `inherited_owner` fills `owner` when the record omits it."""

    path: str
    source: str
    inherited_owner: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class PlanItemView:
    """Row values for one daily plan entry; `path` is the vault-relative link target without `.md`."""

    item_id: str
    title: str
    path: str
    project_title: str
    milestone_title: str | None
    status_mark: str
    due_date: date | None


@dataclass(frozen=True, slots=True, kw_only=True)
class PlanBlockerView:
    """Row values for one blocker under active resolution."""

    blocker_id: str
    title: str
    path: str
    impact: str
    owner: str
    resolved_when: str


@dataclass(frozen=True, slots=True, kw_only=True)
class DailyPlanDocument:
    """Daily plan DTO plus the display values and frontmatter the Markdown record carries."""

    plan: DailyPlan
    owner: str
    tags: tuple[str, ...]
    maturity: str
    record_version: int
    items: tuple[PlanItemView, ...]
    blockers: tuple[PlanBlockerView, ...]
