"""Responsibility: Represent an immutable ToolResultProcessing DTO.
Public interface:
`-- ToolResultProcessing
    +-- message
    +-- payload
    +-- progress
    +-- screen_id
    +-- session_id
    +-- stage
    +-- status
    `-- tool

ToolResultProcessing DTO.
"""

from collections.abc import Mapping
from typing import Literal

from pydantic import UUID7, JsonValue
from pydantic.dataclasses import dataclass

from daily_tasks.core.planning.tool_progress import ToolProgress
from daily_tasks.core.records.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class ToolResultProcessing:
    """Work is still running; call again."""

    tool: str
    status: Literal["processing"]
    session_id: UUID7
    screen_id: str | None
    stage: str
    message: str
    progress: ToolProgress | None
    payload: Mapping[str, JsonValue] | None
