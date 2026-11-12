"""Responsibility: Answer MCP JSON-RPC 2.0 messages by dispatching tool calls to the planning dispatcher.
Public interface:
`-- McpServer
    +-- PROTOCOL_VERSION
    +-- handle(message)
    `-- new(tools, version, secrets, setup)
"""

import json
import logging
import time
from collections.abc import Mapping, Sequence
from typing import ClassVar, Final, final

from pydantic import JsonValue

from daily_tasks.core.planning.planning_dispatcher import PlanningDispatcher
from daily_tasks.core.planning.planning_tools import ToolBody
from daily_tasks.transports.mcp.secret_capturer import SecretCapturer
from daily_tasks.transports.mcp.setup_handler import SetupHandler
from daily_tasks.transports.mcp.tool_definitions import (
    CONFIGURE_VAULT_TOOL,
    SECRET_TOOL,
    SECRET_TOOL_DEFINITIONS,
    SETUP_STATUS_TOOL,
    SETUP_TOOL_DEFINITIONS,
    TOOL_DEFINITIONS,
)
from daily_tasks.transports.mcp.types import VaultSetupSpec

_LOGGER: Final = logging.getLogger(__name__)
_OPERATION: Final = "mcp.request"
_PARSE_ERROR: Final = -32700
_INVALID_REQUEST: Final = -32600
_METHOD_NOT_FOUND: Final = -32601
_INVALID_PARAMS: Final = -32602


def _error(request_id: JsonValue, code: int, message: str) -> dict[str, JsonValue]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def _string(arguments: Mapping[str, JsonValue], key: str) -> str | None:
    value = arguments.get(key)
    return value if isinstance(value, str) else None


def _strings(arguments: Mapping[str, JsonValue], key: str) -> Sequence[str] | None:
    value = arguments.get(key, [])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return None
    return [item for item in value if isinstance(item, str)]


def _objects(arguments: Mapping[str, JsonValue], key: str) -> Sequence[Mapping[str, JsonValue]] | None:
    value = arguments.get(key, [])
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        return None
    return [item for item in value if isinstance(item, dict)]


def _optional_string(arguments: Mapping[str, JsonValue], key: str) -> tuple[bool, str | None]:
    if key not in arguments or arguments[key] is None:
        return True, None
    value = arguments[key]
    return (True, value) if isinstance(value, str) else (False, None)


def _call_configure_vault(setup: SetupHandler, arguments: Mapping[str, JsonValue]) -> ToolBody | None:
    confirmed = arguments.get("confirmed")
    if not isinstance(confirmed, bool):
        return None
    scope = arguments.get("scope", "vault")
    if not isinstance(scope, str):
        return None
    lookback = arguments.get("initial_lookback_days", 7)
    if not isinstance(lookback, int) or isinstance(lookback, bool):
        return None
    set_default = arguments.get("set_default_vault", True)
    if not isinstance(set_default, bool):
        return None
    str_fields: dict[str, str | None] = {}
    for field in (
        "vault_root",
        "user_name",
        "user_email",
        "timezone",
        "projects_root",
        "daily_plans_relative",
        "templates_dir",
    ):
        valid, extracted = _optional_string(arguments, field)
        if not valid:
            return None
        str_fields[field] = extracted
    priorities = _strings(arguments, "priorities") if "priorities" in arguments else None
    if "priorities" in arguments and priorities is None:
        return None
    standalone = _strings(arguments, "standalone_sources") if "standalone_sources" in arguments else None
    if "standalone_sources" in arguments and standalone is None:
        return None
    disabled = _strings(arguments, "disabled_sources") if "disabled_sources" in arguments else None
    if "disabled_sources" in arguments and disabled is None:
        return None
    conns = _objects(arguments, "harness_connections") if "harness_connections" in arguments else None
    if "harness_connections" in arguments and conns is None:
        return None
    return setup.configure_vault(
        VaultSetupSpec(
            confirmed=confirmed,
            scope=scope,
            vault_root=str_fields["vault_root"],
            user_name=str_fields["user_name"],
            user_email=str_fields["user_email"],
            timezone=str_fields["timezone"],
            priorities=priorities,
            projects_root=str_fields["projects_root"],
            daily_plans_relative=str_fields["daily_plans_relative"],
            templates_dir=str_fields["templates_dir"],
            harness_connections=conns,
            standalone_sources=standalone,
            disabled_sources=disabled,
            initial_lookback_days=lookback,
            set_default_vault=set_default,
        )
    )


@final
class McpServer:
    """Borrow `tools`; emit one structured log record per request, never with arguments or screens."""

    PROTOCOL_VERSION: ClassVar[str] = "2025-06-18"

    def __init__(
        self,
        tools: PlanningDispatcher,
        version: str,
        secrets: SecretCapturer | None = None,
        setup: SetupHandler | None = None,
    ) -> None:
        """Keep the collaborators; `version` is reported as `serverInfo.version`."""
        self._tools = tools
        self._version = version
        self._secrets = secrets
        self._setup = setup
        self._definitions = (
            *TOOL_DEFINITIONS,
            *(SECRET_TOOL_DEFINITIONS if secrets is not None else ()),
            *(SETUP_TOOL_DEFINITIONS if setup is not None else ()),
        )
        self._tool_names = frozenset(str(tool["name"]) for tool in self._definitions)

    async def handle(self, message: str) -> str | None:
        """Return the JSON-RPC response line for `message`, or None for notifications."""
        started = time.monotonic()
        try:
            request = json.loads(message)
        except json.JSONDecodeError:
            _LOGGER.warning("unparseable message", extra={"operation": _OPERATION, "fields": {"bytes": len(message)}})
            return json.dumps(_error(None, _PARSE_ERROR, "Parse error"))
        if not isinstance(request, dict) or request.get("jsonrpc") != "2.0" or "method" not in request:
            return json.dumps(_error(None, _INVALID_REQUEST, "Invalid Request"))
        method = request["method"]
        if "id" not in request:
            _LOGGER.debug("notification", extra={"operation": _OPERATION, "fields": {"method": str(method)}})
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
        summary = (
            f"mcp request {fields['request_id']} {fields['method']} {fields['tool']} -> {fields['status']} "
            f"(session {fields['session_id']}, {fields['elapsed_ms']} ms)"
        )
        _LOGGER.info(summary, extra={"operation": _OPERATION, "fields": fields})
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
            return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": list(self._definitions)}}
        if method != "tools/call":
            return _error(request_id, _METHOD_NOT_FOUND, f"Method not found: {method}")
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if not isinstance(name, str) or name not in self._tool_names or not isinstance(arguments, dict):
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
        if name == SETUP_STATUS_TOOL and self._setup is not None:
            if "vault_root" in arguments and not isinstance(arguments["vault_root"], str):
                return None
            return self._setup.setup_status(_string(arguments, "vault_root"))
        if name == CONFIGURE_VAULT_TOOL and self._setup is not None:
            return _call_configure_vault(self._setup, arguments)
        if name == SECRET_TOOL and self._secrets is not None:
            namespace, key = _string(arguments, "namespace"), _string(arguments, "key")
            if not namespace or not key:
                return None
            prompt, provider = _string(arguments, "prompt_message"), _string(arguments, "provider")
            return await self._secrets.capture_secret(namespace, key, prompt, provider)
        if name == "daily_tasks_start_session":
            messages, checked = _objects(arguments, "messages"), _strings(arguments, "checked_sources")
            if messages is None or checked is None:
                return None
            vault_root = _string(arguments, "vault_root")
            return await tools.start_session(
                _string(arguments, "date"),
                _string(arguments, "focus"),
                messages,
                checked,
                vault_root=vault_root,
            )
        if name == "daily_tasks_get_fetch_window":
            sources = _strings(arguments, "sources") if "sources" in arguments else ("gmail", "slack")
            vault_root = _string(arguments, "vault_root")
            return tools.get_fetch_window(sources, vault_root=vault_root) if sources else None
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
