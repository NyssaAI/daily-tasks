# Responsibility: Represent an immutable StateGraphContext DTO.
# Public interface:
# `-- StateGraphContext
#     +-- built_at
#     +-- daily_plans_root
#     +-- inventory_hash
#     +-- local_date
#     +-- projects_root
#     +-- sources
#     +-- timezone
#     +-- user
#     `-- workspace_root
"""StateGraphContext DTO."""

from datetime import date

from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.graph_user import GraphUser
from daily_tasks.domain.record_source_status import RecordSourceStatus
from daily_tasks.domain.utc_timestamp import UtcTimestamp


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
