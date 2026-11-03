# Responsibility: Prove a full MCP planning session over stdio reads a vault, adjudicates and writes on confirm only.
# Public interface:
# (none)
"""End-to-end: JSON-RPC lines in, Markdown records, daily plan, decision log, suggestions and cursors out."""

import asyncio
import io
import json
import shutil
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from itertools import count
from pathlib import Path
from uuid import UUID

from nyssa_ai_result import Result, ok
from pydantic import JsonValue, TypeAdapter

from conftest import SPECS_ROOT
from daily_tasks.domain import FetchCursor, FetchCursors, GraphUser, Message
from daily_tasks.ports import FetchBatch
from daily_tasks.server import MarkdownWorkspaceReader, McpServer, PlanningTools, ServerSettings, serve_stdio
from daily_tasks.storage.cursor_store import CursorStore
from daily_tasks.storage.markdown_file_store import MarkdownFileStore

NOW = datetime(2026, 11, 3, 14, 30, tzinfo=UTC)
PROJECT = "projects/2026.10.20-daily-tasks-mcp-server"
MILESTONE = f"{PROJECT}/m2-planning-session-spike"
TASK_ID = "019a4b2c-1f00-7a10-8000-000000000003"
BLOCKER_ID = "019a4b2c-1f00-7a10-8000-000000000005"


@dataclass
class _RecordingLogger:
    records: list[tuple[str, str, Mapping[str, object]]] = field(default_factory=list)

    def debug(self, message: str, fields: Mapping[str, object] | None = None, operation: str = "") -> None:
        self.records.append(("debug", message, fields or {}))

    def info(self, message: str, fields: Mapping[str, object] | None = None, operation: str = "") -> None:
        self.records.append(("info", message, fields or {}))

    def warn(self, message: str, fields: Mapping[str, object] | None = None, operation: str = "") -> None:
        self.records.append(("warn", message, fields or {}))

    def error(
        self,
        message: str,
        error: BaseException | None = None,
        fields: Mapping[str, object] | None = None,
        operation: str = "",
    ) -> None:
        self.records.append(("error", message, fields or {}))


@dataclass
class _Inbox:
    """Communication source returning one message that says the OAuth verification blocker is resolved."""

    name: str = "gmail"

    async def fetch_new_messages(self, since: FetchCursors) -> Result[FetchBatch]:
        message = TypeAdapter(Message).validate_python(
            {
                "id": "gmail:m1",
                "source": "gmail",
                "external_id": "m1",
                "thread_id": "gmail-thread:m1",
                "received_at": "2026-11-03T12:00:00Z",
                "from": {"name": "Sarah", "address": "sarah@example.com"},
                "to": [{"name": "Jordan", "address": "jordan@example.com"}],
                "cc": [],
                "channel": None,
                "subject": "Google OAuth app verification",
                "snippet": "Google approved the OAuth app.",
                "body": f"Google OAuth app verification is resolved. ref {BLOCKER_ID}",
                "body_format": "text",
                "attachments": [],
                "url": None,
                "fetched_at": "2026-11-03T14:00:00Z",
            }
        )
        cursor = FetchCursor(since=NOW, last_external_id="m1", last_run_at=NOW, last_status="ok", last_error=None)
        return ok(FetchBatch(messages=(message,), cursors=FetchCursors(workspace_root="", cursors={"gmail": cursor})))


def _vault(root: Path) -> None:
    for relative, sample in (
        (f"{PROJECT}/project-index.md", "5-sample-project-index.md"),
        (f"{MILESTONE}/m2-planning-session-spike.md", "6-sample-milestone.md"),
        (f"{MILESTONE}/t1-wire-gmail-connector.md", "4-sample-task.md"),
        (f"{PROJECT}/blockers/b1-google-oauth-app-verification.md", "7-sample-blocker.md"),
    ):
        (root / relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SPECS_ROOT / sample, root / relative)
    (root / "daily-plans").mkdir()


def _server(root: Path, logger: _RecordingLogger) -> McpServer:
    settings = ServerSettings(
        workspace_root=root,
        projects_root=root / "projects",
        daily_plans_root=root / "daily-plans",
        state_root=root / ".nyssa-ai/daily-tasks",
        user=GraphUser(name="Jordan", email="jordan@example.com"),
        timezone="America/Chicago",
    )
    numbers = count(1)

    def new_id() -> UUID:
        return UUID(f"019a4b2c-9000-7000-8000-{next(numbers):012x}")

    cursors = CursorStore(settings.state_root, root.as_posix(), logger)
    store = MarkdownFileStore(
        root, logger, lambda: NOW, settings.projects_root, settings.daily_plans_root, settings.state_root
    )
    reader = MarkdownWorkspaceReader(settings, logger, _Inbox(), cursors)
    return McpServer(PlanningTools(settings, reader, store, logger, lambda: NOW, new_id, cursors), logger, "test")


def _call(request_id: int, name: str, **arguments: JsonValue) -> str:
    params = {"name": name, "arguments": arguments}
    return json.dumps({"jsonrpc": "2.0", "id": request_id, "method": "tools/call", "params": params})


def _run(server: McpServer, *lines: str) -> list[dict[str, JsonValue]]:
    out = io.StringIO()
    code = asyncio.run(serve_stdio(server, io.StringIO("\n".join(lines) + "\n"), out))
    assert code == 0
    return [json.loads(line) for line in out.getvalue().splitlines()]


def _body(response: dict[str, JsonValue]) -> dict[str, JsonValue]:
    result = response["result"]
    assert isinstance(result, dict)
    body = result["structuredContent"]
    assert isinstance(body, dict)
    return body


def _screen(body: dict[str, JsonValue]) -> str:
    payload = body["payload"]
    assert isinstance(payload, dict) and isinstance(payload["screen"], str)
    return payload["screen"]


def test_full_planning_session_confirmed_writes_records_plan_and_logs(tmp_path: Path) -> None:
    _vault(tmp_path)
    logger = _RecordingLogger()
    server = _server(tmp_path, logger)

    started = _run(
        server, '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}', _call(2, "daily_tasks_start_session")
    )
    body = _body(started[1])
    session_id = str(body["session_id"])
    screen = _screen(body)
    suggestion_row = next(
        line.split("|")[1].strip() for line in screen.splitlines() if "Blocker" in line and "gmail:m1" in line
    )
    responses = _run(
        server,
        _call(
            3,
            "daily_tasks_execute_operations",
            session_id=session_id,
            original_words=f"{suggestion_row} accept",
            verdicts=[{"row": int(suggestion_row), "verdict": "accept"}],
        ),
        _call(4, "daily_tasks_advance_screen", session_id=session_id, target_screen=2),
        _call(
            5,
            "daily_tasks_execute_operations",
            session_id=session_id,
            original_words="gmail task today",
            operations=[
                {
                    "kind": "assign-to-day",
                    "row": 1,
                    "item_type": "task",
                    "item_id": TASK_ID,
                    "local_date": "2026-11-03",
                }
            ],
        ),
        _call(6, "daily_tasks_advance_screen", session_id=session_id, target_screen=3),
        _call(7, "daily_tasks_confirm_plan", session_id=session_id, confirmed=True),
    )

    statuses = [_body(r)["status"] for r in responses]
    assert statuses == ["ok"] * 5, [_body(r)["message"] for r in responses]
    blocker_text = (tmp_path / f"{PROJECT}/blockers/b1-google-oauth-app-verification.md").read_text(encoding="utf-8")
    assert "blocker-state: resolved" in blocker_text
    plan = (tmp_path / "daily-plans/2026.11.03-daily-plan.md").read_text(encoding="utf-8")
    assert "Wire Gmail connector behind Communication-Port" in plan and "## Decisions" in plan
    state = tmp_path / ".nyssa-ai/daily-tasks"
    decisions = json.loads((state / "decision-log.json").read_text(encoding="utf-8"))["entries"]
    assert [d["verdict"] for d in decisions] == ["accept", None]
    assert json.loads((state / "suggestions.json").read_text(encoding="utf-8"))["suggestions"] == []
    assert (
        json.loads((state / "fetch-cursors.json").read_text(encoding="utf-8"))["cursors"]["gmail"]["last_external_id"]
        == "m1"
    )
    assert (state / "sessions/2026.11.03.json").exists()
    handled = [f for level, msg, f in logger.records if msg.startswith("mcp request")]
    assert [f["status"] for f in handled][-1] == "ok" and handled[-1]["session_id"] == session_id


def test_full_planning_session_cancelled_writes_nothing(tmp_path: Path) -> None:
    _vault(tmp_path)
    before = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*"))
    server = _server(tmp_path, _RecordingLogger())

    session_id = str(_body(_run(server, _call(1, "daily_tasks_start_session"))[0])["session_id"])
    responses = _run(
        server,
        _call(2, "daily_tasks_advance_screen", session_id=session_id, target_screen=3),
        _call(3, "daily_tasks_confirm_plan", session_id=session_id, confirmed=False),
        _call(4, "daily_tasks_cancel_session", session_id=session_id),
        _call(5, "daily_tasks_get_session_state", session_id=session_id),
    )

    assert [_body(r)["status"] for r in responses] == ["ok", "error", "ok", "error"]
    assert "not_confirmed" in str(_body(responses[1])["message"])
    assert sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*")) == before
