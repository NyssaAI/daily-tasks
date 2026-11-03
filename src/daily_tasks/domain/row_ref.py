# Responsibility: Represent an immutable RowRef DTO.
# Public interface:
# `-- RowRef
#     +-- id
#     `-- kind
"""RowRef DTO."""

from typing import Literal

from pydantic import UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class RowRef:
    """Item a numbered row points at."""

    kind: Literal["task", "blocker", "suggestion", "milestone", "project"]
    id: UUID7
