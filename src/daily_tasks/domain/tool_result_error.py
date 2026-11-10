"""Responsibility: Represent an immutable ToolResultError DTO.
Public interface:
`-- ToolResultError
    +-- code
    +-- message
    +-- payload
    +-- screen_id
    +-- session_id
    +-- stage
    +-- status
    `-- tool

ToolResultError DTO.
"""

from collections.abc import Mapping
from typing import Literal

from pydantic import MISSING, UUID7, JsonValue
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class ToolResultError:
    """Tool failed with an error code."""

    tool: str
    status: Literal["error"]
    session_id: UUID7 | None
    screen_id: str | None
    stage: str | None
    message: str
    code: str | MISSING = MISSING
    payload: Mapping[str, JsonValue] | None
