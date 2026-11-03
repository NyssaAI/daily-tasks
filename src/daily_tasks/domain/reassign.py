# Responsibility: Represent an immutable Reassign DTO.
# Public interface:
# `-- Reassign
#     +-- item_id
#     +-- item_type
#     +-- kind
#     +-- owner
#     `-- row
"""Reassign DTO."""

from typing import Literal

from pydantic import UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.item_type import ItemType


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class Reassign:
    """Change the owner of a task or blocker."""

    kind: Literal["reassign"]
    row: int
    item_type: ItemType
    item_id: UUID7
    owner: str
