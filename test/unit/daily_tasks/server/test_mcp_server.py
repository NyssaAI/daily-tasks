# Responsibility: Prove the MCP server answers JSON-RPC 2.0 correctly and keeps stdout free of logs.
# Public interface:
# (none)
"""Protocol handling through `McpServer.handle` and the `daily-tasks-mcp` CLI with in-memory pipes."""

import asyncio
import io
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest
from nyssa_ai_result import Result, fail
from pydantic import JsonValue

from daily_tasks.cli import cli
from daily_tasks.domain import GraphUser
from daily_tasks.server import McpServer, PlanningTools, ServerSettings, WorkspaceSnapshot
from daily_tasks.storage.markdown_file_store import MarkdownFileStore

NOW = datetime(2026, 11, 3, 14, 30, tzinfo=UTC)


class _QuietLogger:
    def debug(self, message: str, fields: Mapping[str, object] | None = None, operation: str = "") -> None:
        pass

    def info(self, message: str, fields: Mapping[str, object] | None = None, operation: str = "") -> None:
        pass

    def warn(self, message: str, fields: Mapping[str, object] | None = None, operation: str = "") -> None:
        pass

    def error(
        self,
        message: str,
        error: BaseException | None = None,
        fields: Mapping[str, object] | None = None,
        operation: str = "",
    ) -> None:
        pass


class _UnavailableReader:
    async def read(self, now: datetime) -> Result[WorkspaceSnapshot]:
        return fail("projects root not found", "Unavailable")


def _server(root: Path) -> McpServer:
    settings = ServerSettings(
        workspace_root=root,
        projects_root=root / "projects",
        daily_plans_root=root / "daily-plans",
        state_root=root / ".nyssa-ai/daily-tasks",
        user=GraphUser(name="Jordan", email="jordan@example.com"),
        timezone="America/Chicago",
    )
    logger = _QuietLogger()
    store = MarkdownFileStore(root, logger, lambda: NOW)
    new_id = lambda: UUID("019a4b2c-9000-7000-8000-000000000001")  # noqa: E731
    tools = PlanningTools(settings, _UnavailableReader(), store, logger, lambda: NOW, new_id)
    return McpServer(tools, logger, "1.2.3")


def _handle(server: McpServer, request: Mapping[str, JsonValue] | str) -> dict[str, JsonValue] | None:
    text = request if isinstance(request, str) else json.dumps(request)
    response = asyncio.run(server.handle(text))
    return None if response is None else json.loads(response)


def test_initialize_reports_protocol_and_tools_capability(tmp_path: Path) -> None:
    response = _handle(_server(tmp_path), {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})

    assert response == {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "protocolVersion": McpServer.PROTOCOL_VERSION,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "daily-tasks", "version": "1.2.3"},
        },
    }


def test_tools_list_names_every_planning_tool(tmp_path: Path) -> None:
    response = _handle(_server(tmp_path), {"jsonrpc": "2.0", "id": "a", "method": "tools/list"})

    assert response is not None and isinstance(response["result"], dict)
    tools = response["result"]["tools"]
    assert isinstance(tools, list)
    assert [t["name"] for t in tools if isinstance(t, dict)] == [
        "daily_tasks_start_session",
        "daily_tasks_get_session_state",
        "daily_tasks_execute_operations",
        "daily_tasks_advance_screen",
        "daily_tasks_confirm_plan",
        "daily_tasks_cancel_session",
    ]


def test_notification_gets_no_response(tmp_path: Path) -> None:
    assert _handle(_server(tmp_path), {"jsonrpc": "2.0", "method": "notifications/initialized"}) is None


@pytest.mark.parametrize(
    ("request_text", "code"),
    [
        ("{not json", -32700),
        (json.dumps({"id": 1, "method": "ping"}), -32600),
        (json.dumps({"jsonrpc": "2.0", "id": 1, "method": "resources/list"}), -32601),
        (json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "nope"}}), -32602),
        (
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {"name": "daily_tasks_advance_screen", "arguments": {"session_id": "x"}},
                }
            ),
            -32602,
        ),
    ],
)
def test_invalid_request_returns_json_rpc_error(tmp_path: Path, request_text: str, code: int) -> None:
    response = _handle(_server(tmp_path), request_text)

    assert response is not None and isinstance(response["error"], dict)
    assert response["error"]["code"] == code


def test_tool_failure_is_tool_error_result_not_protocol_error(tmp_path: Path) -> None:
    request = {"jsonrpc": "2.0", "id": 9, "method": "tools/call", "params": {"name": "daily_tasks_start_session"}}

    response = _handle(_server(tmp_path), request)

    assert response is not None and isinstance(response["result"], dict)
    result = response["result"]
    assert result["isError"] is True
    body = result["structuredContent"]
    assert isinstance(body, dict)
    assert (body["status"], body["code"], body["message"]) == ("error", "Unavailable", "projects root not found")


def test_unknown_session_is_reported_as_not_found(tmp_path: Path) -> None:
    arguments = {"session_id": "019a4b2c-9000-7000-8000-0000000000ff"}
    request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "daily_tasks_get_session_state", "arguments": arguments},
    }

    response = _handle(_server(tmp_path), request)

    assert response is not None and isinstance(response["result"], dict)
    body = response["result"]["structuredContent"]
    assert isinstance(body, dict) and body["code"] == "NotFound"


def test_cli_stdout_carries_only_json_rpc_responses(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / "projects").mkdir()
    lines = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "daily_tasks_start_session"}},
    ]
    stdin = io.StringIO("\n".join(json.dumps(line) for line in lines) + "\n")
    stdout = io.StringIO()
    argv = ["--workspace-root", str(tmp_path), "--user-email", "jordan@example.com", "--timezone", "UTC"]

    code = cli(argv, environ={}, stdin=stdin, stdout=stdout)

    responses = [json.loads(line) for line in stdout.getvalue().splitlines()]
    assert code == 0
    assert [r["id"] for r in responses] == [1, 2]
    assert "server started" in capsys.readouterr().err


def test_cli_without_user_or_timezone_exits_2(tmp_path: Path) -> None:
    stdout = io.StringIO()

    code = cli(["--workspace-root", str(tmp_path)], environ={}, stdin=io.StringIO(""), stdout=stdout)

    assert code == 2 and stdout.getvalue() == ""


def test_start_session_surfaces_malformed_files(tmp_path: Path) -> None:
    (tmp_path / "projects").mkdir()
    (tmp_path / "projects/t1-broken.md").write_text("---\nid: 1\n", encoding="utf-8")
    lines = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "daily_tasks_start_session"}},
    ]
    stdin = io.StringIO("\n".join(json.dumps(line) for line in lines) + "\n")
    stdout = io.StringIO()
    argv = ["--workspace-root", str(tmp_path), "--user-email", "jordan@example.com", "--timezone", "UTC"]

    code = cli(argv, environ={}, stdin=stdin, stdout=stdout)

    assert code == 0
    responses = [json.loads(line) for line in stdout.getvalue().splitlines()]
    result = responses[1]["result"]["structuredContent"]
    assert result["status"] == "ok"
    assert "malformed or unreadable file(s) were skipped" in result["message"]
    payload = result["payload"]
    assert "malformed_files" in payload
    assert len(payload["malformed_files"]) == 1
    assert payload["malformed_files"][0]["path"] == "t1-broken.md"
    assert payload["malformed_files"][0]["code"] == "unclosed-frontmatter"
