# Responsibility: Represent an immutable ProjectNode DTO.
# Public interface:
# `-- ProjectNode
#     +-- directory_date
#     +-- owner
#     +-- ref
#     +-- state
#     `-- title
"""ProjectNode DTO."""

from datetime import date
from pydantic import Field, MISSING
from pydantic.dataclasses import dataclass
from daily_tasks.domain.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class ProjectNode:
    """Project fields the graph keeps in memory."""

    ref: str | MISSING = Field(default=MISSING, alias="$ref")
    title: str
    state: str
    owner: str | MISSING = MISSING
    directory_date: date

