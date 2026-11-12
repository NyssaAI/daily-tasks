"""Responsibility: Represent an immutable StateGraphContext record.
Public interface:
`-- StateGraphContext
    +-- built_at
    +-- daily_plans_root
    +-- inventory_hash
    +-- local_date
    +-- projects_root
    +-- sources
    +-- timezone
    +-- user
    `-- vault_root
"""

from datetime import date

from pydantic.dataclasses import dataclass

from daily_tasks.core.records.dto_config import DTO_CONFIG
from daily_tasks.core.records.graph_user import GraphUser
from daily_tasks.core.records.record_source_status import RecordSourceStatus
from daily_tasks.core.records.utc_timestamp import UtcTimestamp


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class StateGraphContext:
    """Vault roots, user, local day, and inventory hash from which the state graph was built."""

    vault_root: str
    projects_root: str
    daily_plans_root: str
    user: GraphUser
    timezone: str
    local_date: date
    built_at: UtcTimestamp
    inventory_hash: str
    sources: tuple[RecordSourceStatus, ...]
