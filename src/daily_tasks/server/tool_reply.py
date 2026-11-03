# Responsibility: Turn a planning step outcome into the JSON body of a `docs/specs/tool-results.json` result.
# Public interface:
# `-- tool_reply(tool, outcome, session, screen, expected_tool, payload)
"""Conflicts become `refused` results naming the next tool; other failures become `error` results."""

from collections.abc import Mapping
from typing import Final
from uuid import UUID

from nyssa_ai_result import ErrorCategory, Result
from pydantic import JsonValue, TypeAdapter

from daily_tasks.domain import ToolResult, ToolResultError, ToolResultOk, ToolResultRefused
from daily_tasks.session import SessionState

_RESULT: Final[TypeAdapter[ToolResult]] = TypeAdapter(ToolResult)


def tool_reply(
    tool: str,
    outcome: Result[str],
    session: SessionState | None,
    screen: str | None = None,
    expected_tool: str | None = None,
    payload: Mapping[str, JsonValue] | None = None,
) -> dict[str, JsonValue]:
    """Return the result as JSON; `outcome` carries the success message or the failure.

    `screen` (the rendered Markdown) joins `payload` under `screen` on success.
    """
    session_id: UUID | None = session.session.id if session is not None else None
    screen_id = session.session.current_screen or None if session is not None else None
    stage = session.stage.value if session is not None else None
    body: dict[str, JsonValue] = {**(payload or {}), **({"screen": screen} if screen is not None else {})}
    result: ToolResult
    if outcome.ok and session_id is not None and stage is not None:
        result = ToolResultOk(
            tool=tool,
            status="ok",
            session_id=session_id,
            screen_id=screen_id,
            stage=stage,
            message=outcome.value,
            payload=body or None,
        )
    elif not outcome.ok and outcome.category == ErrorCategory.CONFLICT and session_id is not None and stage:
        result = ToolResultRefused(
            tool=tool,
            status="refused",
            session_id=session_id,
            screen_id=screen_id,
            stage=stage,
            message=outcome.message,
            expected_tool=expected_tool,
            payload=body or None,
        )
    else:
        result = ToolResultError(
            tool=tool,
            status="error",
            session_id=session_id,
            screen_id=screen_id,
            stage=stage,
            message=outcome.message if not outcome.ok else outcome.value,
            code=str(outcome.category) if not outcome.ok else "Unexpected",
            payload=body or None,
        )
    dumped: dict[str, JsonValue] = _RESULT.dump_python(result, mode="json", exclude_unset=False)
    return {key: value for key, value in dumped.items() if key != "progress" or value is not None}
