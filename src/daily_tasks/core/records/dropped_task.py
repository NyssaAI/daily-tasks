"""Responsibility: Represent an immutable DroppedTask DTO.
Public interface:
`-- DroppedTask
    +-- reason
    `-- task_id

DroppedTask DTO.
"""

from pydantic import UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.core.records.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class DroppedTask:
    """Task not carried forward, and why."""

    task_id: UUID7
    reason: str
