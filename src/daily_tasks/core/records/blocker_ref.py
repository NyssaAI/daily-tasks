"""Responsibility: Represent an immutable BlockerRef DTO.
Public interface:
`-- BlockerRef
    +-- blocker_id
    `-- blocks

BlockerRef DTO.
"""

from pydantic import UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.core.records.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class BlockerRef:
    """Blocker under active resolution and the records it blocks."""

    blocker_id: UUID7
    blocks: tuple[UUID7, ...]
