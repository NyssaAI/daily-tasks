"""Responsibility: Represent an immutable ToolResultRefused DTO.
Public interface:
`-- ToolResultRefused
    +-- expected_tool
    +-- message
    +-- payload
    +-- screen_id
    +-- session_id
    +-- stage
    +-- status
    `-- tool

ToolResultRefused DTO.
"""

from collections.abc import Mapping
from typing import Literal

from pydantic import UUID7, JsonValue
from pydantic.dataclasses import dataclass

from daily_tasks.core.records.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class ToolResultRefused:
    """Tool call refused in the current session state, naming the tool to call instead."""

    tool: str
    status: Literal["refused"]
    session_id: UUID7
    screen_id: str | None
    stage: str
    message: str
    expected_tool: str | None
    payload: Mapping[str, JsonValue] | None
