# Responsibility: Represent an immutable StateGraphSummary DTO.
# Public interface:
# `-- StateGraphSummary
#     +-- blocked_tasks
#     +-- carried_forward
#     +-- changed_outside_app
#     +-- late_tasks
#     +-- open_blockers
#     +-- open_milestones
#     +-- open_projects
#     +-- open_tasks
#     +-- pending_operations
#     +-- selected_today
#     `-- unreviewed_messages
"""StateGraphSummary DTO."""

from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class StateGraphSummary:
    """Headline counts across the state graph."""

    open_projects: int
    open_milestones: int
    open_tasks: int
    late_tasks: int
    blocked_tasks: int
    open_blockers: int
    selected_today: int
    carried_forward: int
    pending_operations: int
    unreviewed_messages: int
    changed_outside_app: int
