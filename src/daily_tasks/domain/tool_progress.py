# Responsibility: Represent an immutable ToolProgress DTO.
# Public interface:
# `-- ToolProgress
#     +-- sources_done
#     `-- sources_total
"""ToolProgress DTO."""

from pydantic.dataclasses import dataclass
from daily_tasks.domain.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class ToolProgress:
    """Background progress across sources."""

    sources_done: int
    sources_total: int

