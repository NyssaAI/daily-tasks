# Responsibility: Answer MCP JSON-RPC 2.0 messages by dispatching tool calls to the planning tools.
# Public interface:
# `-- McpServer
#     +-- PROTOCOL_VERSION
#     +-- handle(message)
#     `-- new(tools, logger, version)
"""Transport-free MCP protocol handling: `initialize`, `ping`, `tools/list` and `tools/call`."""

import json
import time
from collections.abc import Mapping, Sequence
from typing import ClassVar, Final, final

from pydantic import JsonValue

from daily_tasks.ports import PortLogger
from daily_tasks.server.planning_tools import PlanningTools, ToolBody
from daily_tasks.server.tool_definitions import TOOL_DEFINITIONS

_OPERATION: Final = "mcp.request"
_PARSE_ERROR: Final = -32700
_INVALID_REQUEST: Final = -32600
_METHOD_NOT_FOUND: Final = -32601
_INVALID_PARAMS: Final = -32602
_TOOL_NAMES: Final = frozenset(str(tool["name"]) for tool in TOOL_DEFINITIONS)


def _error(request_id: JsonValue, code: int, message: str) -> dict[str, JsonValue]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def _string(arguments: Mapping[str, JsonValue], key: str) -> str | None:
    value = arguments.get(key)
    return value if isinstance(value, str) else None


def _objects(arguments: Mapping[str, JsonValue], key: str) -> Sequence[Mapping[str, JsonValue]] | None:
    value = arguments.get(key, [])
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        return None
    return [item for item in value if isinstance(item, dict)]


@final
class McpServer:
    """Borrow `tools` and `logger`; one structured log record per request, never with arguments or screens."""

    PROTOCOL_VERSION: ClassVar[str] = "2025-06-18"

    def __init__(self, tools: PlanningTools, logger: PortLogger, version: str) -> None:
        """Keep the collaborators; `version` is reported as `serverInfo.version`."""
        self._tools = tools
        self._logger = logger
        self._version = version

    async def handle(self, message: str) -> str | None:
        """Return the JSON-RPC response line for `message`, or None for notifications."""
        started = time.monotonic()
        try:
            request = json.loads(message)
        except json.JSONDecodeError:
            self._logger.warn("unparseable message", fields={"bytes": len(message)}, operation=_OPERATION)
            return json.dumps(_error(None, _PARSE_ERROR, "Parse error"))
        if not isinstance(request, dict) or request.get("jsonrpc") != "2.0" or "method" not in request:
            return json.dumps(_error(None, _INVALID_REQUEST, "Invalid Request"))
        method = request["method"]
        if "id" not in request:
            self._logger.debug("notification", fields={"method": str(method)}, operation=_OPERATION)
            return None
        request_id: JsonValue = request["id"]
        params = request.get("params") or {}
        response = await self._dispatch(request_id, str(method), params if isinstance(params, dict) else {})
        fields: dict[str, object] = {
            "request_id": str(request_id),
            "method": str(method),
            "outcome": "error" if "error" in response else "ok",
            "elapsed_ms": round((time.monotonic() - started) * 1000, 3),
        }
        result = response.get("result")
        body = result.get("structuredContent") if isinstance(result, dict) else None
        fields["tool"] = str(params.get("name", "")) if isinstance(params, dict) else ""
        fields["session_id"] = str(body.get("session_id")) if isinstance(body, dict) else ""
        fields["status"] = str(body.get("status")) if isinstance(body, dict) else fields["outcome"]
        self._logger.info(
            "mcp request {request_id} {method} {tool} -> {status} (session {session_id}, {elapsed_ms} ms)",
            fields=fields,
            operation=_OPERATION,
        )
        return json.dumps(response, ensure_ascii=False)

    async def _dispatch(self, request_id: JsonValue, method: str, params: dict[str, JsonValue]) -> dict[str, JsonValue]:
        if method == "initialize":
            result: dict[str, JsonValue] = {
                "protocolVersion": self.PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "daily-tasks", "version": self._version},
            }
            return {"jsonrpc": "2.0", "id": request_id, "result": result}
        if method == "ping":
            return {"jsonrpc": "2.0", "id": request_id, "result": {}}
        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": list(TOOL_DEFINITIONS)}}
        if method != "tools/call":
            return _error(request_id, _METHOD_NOT_FOUND, f"Method not found: {method}")
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if not isinstance(name, str) or name not in _TOOL_NAMES or not isinstance(arguments, dict):
            return _error(request_id, _INVALID_PARAMS, f"Unknown tool: {name}")
        body = await self._call(name, arguments)
        if body is None:
            return _error(request_id, _INVALID_PARAMS, f"Invalid arguments for {name}")
        is_error = body.get("status") == "error"
        content: JsonValue = [{"type": "text", "text": json.dumps(body, ensure_ascii=False)}]
        result = {"content": content, "structuredContent": body, "isError": is_error}
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    async def _call(self, name: str, arguments: Mapping[str, JsonValue]) -> ToolBody | None:
        tools = self._tools
        if name == "daily_tasks_start_session":
            return await tools.start_session(_string(arguments, "date"), _string(arguments, "focus"))
        session_id = _string(arguments, "session_id")
        if session_id is None:
            return None
        if name == "daily_tasks_get_session_state":
            return tools.get_session_state(session_id)
        if name == "daily_tasks_cancel_session":
            return tools.cancel_session(session_id)
        if name == "daily_tasks_advance_screen":
            target = arguments.get("target_screen")
            return tools.advance_screen(session_id, target) if isinstance(target, int) else None
        if name == "daily_tasks_confirm_plan":
            confirmed = arguments.get("confirmed")
            return tools.confirm_plan(session_id, confirmed) if isinstance(confirmed, bool) else None
        words, operations, verdicts = (
            _string(arguments, "original_words"),
            _objects(arguments, "operations"),
            _objects(arguments, "verdicts"),
        )
        if words is None or operations is None or verdicts is None:
            return None
        return tools.execute_operations(session_id, words, operations, verdicts)
