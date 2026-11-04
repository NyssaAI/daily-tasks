# Responsibility: Prove the MCP server answers JSON-RPC 2.0 correctly and keeps stdout free of logs.
# Public interface:
# (none)
"""Protocol handling through `McpServer.handle` and the `daily-tasks-mcp` CLI with in-memory pipes."""

import asyncio
import io
import json
import threading
import urllib.parse
import urllib.request
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest
from nyssa_ai_configuration import BootstrapOptions, KeyringInMemory, LoopbackSecretInputProvider
from nyssa_ai_result import Ok, Result, fail, ok
from pydantic import JsonValue

from daily_tasks.cli import cli
from daily_tasks.credentials import SecretCaptureService, SecretResolver
from daily_tasks.domain import GraphUser
from daily_tasks.server import McpServer, PlanningTools, SecretTools, ServerSettings, WorkspaceSnapshot
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


def _server(root: Path, secrets: SecretTools | None = None) -> McpServer:
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
    return McpServer(tools, logger, "1.2.3", secrets)


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
        "daily_tasks_get_fetch_window",
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


SECRET = "bws-machine-token-0123456789"


class _RecordingLogger(_QuietLogger):
    def __init__(self) -> None:
        self.records: list[tuple[str, str, Mapping[str, object]]] = []

    def info(self, message: str, fields: Mapping[str, object] | None = None, operation: str = "") -> None:
        self.records.append(("info", message, fields or {}))

    def warn(self, message: str, fields: Mapping[str, object] | None = None, operation: str = "") -> None:
        self.records.append(("warn", message, fields or {}))


class _NoBrowser:
    def open_url(self, url: str) -> Result[None]:
        return ok(None)


def _secret_options(root: Path) -> BootstrapOptions:
    return BootstrapOptions(
        application_name="daily-tasks-test",
        configuration_directory=str(root / "config"),
        manifest_path=str(root / "manifest.json"),
    )


def _capture_call(arguments: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    return {
        "jsonrpc": "2.0",
        "id": 7,
        "method": "tools/call",
        "params": {"name": "daily_tasks_capture_secret", "arguments": dict(arguments)},
    }


def test_tools_list_names_capture_secret_when_secret_tools_are_wired(tmp_path: Path) -> None:
    secrets = SecretTools(lambda: fail("unused", "Unavailable"), _QuietLogger())

    response = _handle(_server(tmp_path, secrets), {"jsonrpc": "2.0", "id": 1, "method": "tools/list"})

    assert response is not None and isinstance(response["result"], dict)
    tools = response["result"]["tools"]
    assert isinstance(tools, list)
    names = [t["name"] for t in tools if isinstance(t, dict)]
    assert names[-1] == "daily_tasks_capture_secret" and len(names) == 8


def test_capture_secret_tool_stores_secret_from_loopback_and_replies_with_receipt_only(tmp_path: Path) -> None:
    keyring, logger, status = KeyringInMemory(), _RecordingLogger(), io.StringIO()
    loopback = LoopbackSecretInputProvider(_NoBrowser(), status)

    def open_service() -> Result[SecretCaptureService]:
        return SecretCaptureService.create(_secret_options(tmp_path), logger, None, keyring, loopback, status)

    def user_submits_form() -> None:
        url = loopback.wait_for_url()
        assert url is not None
        form = {"session_token": loopback.session_token, "secret": SECRET, "confirm_secret": SECRET}
        request = urllib.request.Request(url, data=urllib.parse.urlencode(form).encode(), method="POST")
        with urllib.request.urlopen(request, timeout=5) as response:
            response.read()

    user = threading.Thread(target=user_submits_form)
    user.start()
    server = _server(tmp_path, SecretTools(open_service, logger, timeout_seconds=10))

    response = _handle(server, _capture_call({"namespace": "vault", "key": "bws-access-token"}))
    user.join(timeout=10)

    assert response is not None and isinstance(response["result"], dict)
    body = response["result"]["structuredContent"]
    assert isinstance(body, dict) and body["status"] == "ok"
    assert isinstance(body["payload"], dict) and isinstance(body["payload"]["receipt"], dict)
    receipt = body["payload"]["receipt"]
    assert set(receipt) == {"namespace", "key", "provider", "stored_at"}
    assert (receipt["namespace"], receipt["key"], receipt["provider"]) == ("vault", "bws-access-token", "aesLocal")
    assert SECRET not in json.dumps(response) + repr(logger.records) + status.getvalue()
    disk = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in tmp_path.rglob("*") if p.is_file())
    assert SECRET not in disk
    resolver = SecretResolver.create(
        "daily-tasks-test", str(tmp_path / "config"), logger, keyring, {}, str(tmp_path / "manifest.json")
    )
    assert isinstance(resolver, Ok)
    resolved = resolver.value.resolve("vault", "bws-access-token")
    assert isinstance(resolved, Ok) and resolved.value.reveal() == SECRET


def test_capture_secret_tool_store_failure_is_tool_error(tmp_path: Path) -> None:
    logger = _RecordingLogger()
    secrets = SecretTools(lambda: fail("keyring locked", "Unavailable"), logger)

    response = _handle(_server(tmp_path, secrets), _capture_call({"namespace": "communication", "key": "slack"}))

    assert response is not None and isinstance(response["result"], dict)
    assert response["result"]["isError"] is True
    body = response["result"]["structuredContent"]
    assert isinstance(body, dict)
    assert (body["status"], body["code"], body["message"]) == ("error", "Unavailable", "keyring locked")
    assert logger.records[-1][0:2] == ("warn", "secret not captured")


def test_capture_secret_tool_missing_key_is_invalid_params(tmp_path: Path) -> None:
    secrets = SecretTools(lambda: fail("unused", "Unavailable"), _QuietLogger())

    response = _handle(_server(tmp_path, secrets), _capture_call({"namespace": "communication"}))

    assert response is not None and isinstance(response["error"], dict)
    assert response["error"]["code"] == -32602


def test_capture_secret_tool_is_unknown_without_secret_tools(tmp_path: Path) -> None:
    response = _handle(_server(tmp_path), _capture_call({"namespace": "communication", "key": "slack"}))

    assert response is not None and isinstance(response["error"], dict)
    assert response["error"]["code"] == -32602
