# Responsibility: Represent an immutable ToolResultOk DTO.
# Public interface:
# `-- ToolResultOk
#     +-- message
#     +-- payload
#     +-- progress
#     +-- screen_id
#     +-- session_id
#     +-- stage
#     +-- status
#     `-- tool
"""ToolResultOk DTO."""

from collections.abc import Mapping
from typing import Literal

from pydantic import MISSING, UUID7, JsonValue
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.tool_progress import ToolProgress


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class ToolResultOk:
    """Tool completed and returns its payload."""

    tool: str
    status: Literal["ok"]
    session_id: UUID7
    screen_id: str | None
    stage: str
    message: str
    progress: ToolProgress | None | MISSING = MISSING
    payload: Mapping[str, JsonValue] | None
