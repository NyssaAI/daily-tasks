# Responsibility: Represent an immutable BlockerNode DTO.
# Public interface:
# `-- BlockerNode
#     +-- owner
#     +-- project_id
#     +-- ref
#     +-- state
#     `-- title
"""BlockerNode DTO."""

from pydantic import MISSING, UUID7, Field
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class BlockerNode:
    """Blocker fields the graph keeps in memory."""

    ref: str | MISSING = Field(default=MISSING, alias="$ref")
    project_id: UUID7
    title: str
    state: str
    owner: str
