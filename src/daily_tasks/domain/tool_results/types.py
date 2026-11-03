# Responsibility: Group the MCP tool result wrapper DTOs.
# Public interface:
# +-- ToolProgress
# |   +-- sources_done
# |   `-- sources_total
# +-- ToolResult
# +-- ToolResultError
# |   +-- code
# |   +-- message
# |   +-- payload
# |   +-- screen_id
# |   +-- session_id
# |   +-- stage
# |   +-- status
# |   `-- tool
# +-- ToolResultOk
# |   +-- message
# |   +-- payload
# |   +-- progress
# |   +-- screen_id
# |   +-- session_id
# |   +-- stage
# |   +-- status
# |   `-- tool
# +-- ToolResultProcessing
# |   +-- message
# |   +-- payload
# |   +-- progress
# |   +-- screen_id
# |   +-- session_id
# |   +-- stage
# |   +-- status
# |   `-- tool
# +-- ToolResultRefused
# |   +-- expected_tool
# |   +-- message
# |   +-- payload
# |   +-- screen_id
# |   +-- session_id
# |   +-- stage
# |   +-- status
# |   `-- tool
# `-- ToolResults
"""ToolResult: a discriminated union of processing, ok, refused and error responses."""

from collections.abc import Mapping
from typing import Annotated, Literal

from pydantic import MISSING, UUID7, Field, JsonValue
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class ToolProgress:
    """Background progress across sources."""

    sources_done: int
    sources_total: int


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


type ToolResult = Annotated[
    ToolResultProcessing | ToolResultOk | ToolResultRefused | ToolResultError, Field(discriminator="status")
]

type ToolResults = tuple[ToolResult, ...]
