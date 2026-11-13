"""Responsibility: Prove a full MCP planning session over stdio reads a vault, adjudicates, and writes on confirm only.
Public interface:
+-- BLOCKER_ID
+-- MILESTONE
+-- NOW
+-- PROJECT
+-- TASK_ID
+-- test_full_planning_session_cancelled_writes_nothing(tmp_path)
+-- test_full_planning_session_confirmed_writes_records_plan_and_logs_without_touching_vault_nyssa_ai(tmp_path)
`-- test_full_planning_session_dispatcher_recovers_after_unconfirmed_attempt(tmp_path)

End-to-end use-case: JSON-RPC lines in, Markdown records + daily plan in vault_root, and runtime state in runtime_root.
"""

import asyncio
import io
import json
import logging
import shutil
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from itertools import count
from pathlib import Path
from typing import Final
from uuid import UUID

from nyssa_ai_result import Result, ok
from pydantic import JsonValue, TypeAdapter

from daily_tasks.communications.cursor_store_json import CursorStoreJson
from daily_tasks.communications.suggestions_repository_json import SuggestionsRepositoryJson
from daily_tasks.core.communications import CommunicationMessage, FetchBatch, FetchCursor, FetchCursors
from daily_tasks.core.planning.planning_tools import PlanningTools
from daily_tasks.core.planning.planning_tools_dispatcher import PlanningToolsDispatcher
from daily_tasks.core.planning.types import PlanningContext
from daily_tasks.core.records.graph_user import GraphUser
from daily_tasks.hosting.types import ServerOverrides, ServerSettings
from daily_tasks.hosting.vault_collaborator_resolver import VaultCollaboratorResolver
from daily_tasks.hosting.vault_reader_markdown import VaultReaderMarkdown
from daily_tasks.planning.decision_log_store_json import DecisionLogStoreJson
from daily_tasks.planning.session_committer_local import SessionCommitterLocal
from daily_tasks.planning.session_store_json import SessionStoreJson
from daily_tasks.records.file_store_local import FileStoreLocal
from daily_tasks.transports.mcp.mcp_server import McpServer
from daily_tasks.transports.mcp.serve_stdio import serve_stdio

_SAMPLES_ROOT: Final[Path] = Path(__file__).resolve().parents[2] / "unit" / "daily_tasks" / "samples"
NOW = datetime(2026, 11, 3, 14, 30, tzinfo=UTC)
PROJECT = "1-projects/2026.10.20-daily-tasks-mcp-server"
MILESTONE = f"{PROJECT}/m2-planning-session-spike"
TASK_ID = "019a4b2c-1f00-7a10-8000-000000000003"
BLOCKER_ID = "019a4b2c-1f00-7a10-8000-000000000005"


@contextmanager
def _captured_logs() -> Iterator[list[tuple[str, str, Mapping[str, object]]]]:
    records: list[tuple[str, str, Mapping[str, object]]] = []

    class _Handler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            level = "error" if record.levelno >= logging.ERROR else "info"
            raw_fields = record.__dict__.get("fields")
            fields: dict[str, object] = dict(raw_fields) if isinstance(raw_fields, Mapping) else {}
            records.append((level, record.getMessage(), fields))

    package_logger = logging.getLogger("daily_tasks")
    previous_level = package_logger.level
    previous_propagate = package_logger.propagate
    handler = _Handler(level=logging.DEBUG)
    package_logger.setLevel(logging.DEBUG)
    package_logger.propagate = False
    package_logger.addHandler(handler)
    try:
        yield records
    finally:
        package_logger.removeHandler(handler)
        package_logger.setLevel(previous_level)
        package_logger.propagate = previous_propagate


@dataclass
class _Inbox:
    """Communication client returning one message stating the OAuth verification blocker is resolved."""

    name: str = "gmail"

    async def fetch_new_messages(self, since: FetchCursors) -> Result[FetchBatch]:
        message = TypeAdapter(CommunicationMessage).validate_python(
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
        return ok(FetchBatch(messages=(message,), cursors=FetchCursors(vault_root="", cursors={"gmail": cursor})))


def _vault(vault_root: Path) -> None:
    for relative, sample in (
        (f"{PROJECT}/project-index.md", "5-sample-project-index.md"),
        (f"{MILESTONE}/m2-planning-session-spike.md", "6-sample-milestone.md"),
        (f"{MILESTONE}/t1-wire-gmail-connector.md", "4-sample-task.md"),
        (f"{PROJECT}/blockers/b1-google-oauth-app-verification.md", "7-sample-blocker.md"),
    ):
        (vault_root / relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(_SAMPLES_ROOT / sample, vault_root / relative)
    (vault_root / "2-areas" / "daily-plans").mkdir(parents=True)


def _server(vault_root: Path, runtime_root: Path) -> McpServer:
    settings = ServerSettings(
        vault_root=vault_root,
        projects_root=vault_root / "1-projects",
        daily_plans_root=vault_root / "2-areas" / "daily-plans",
        runtime_root=runtime_root,
        user=GraphUser(name="Jordan", email="jordan@example.com"),
        timezone="America/Chicago",
    )
    numbers = count(1)

    def new_id() -> UUID:
        return UUID(f"019a4b2c-9000-7000-8000-{next(numbers):012x}")

    vault_key = vault_root.as_posix()
    cursors = CursorStoreJson(runtime_root, vault_key)
    file_store = FileStoreLocal(
        vault_root,
        lambda: NOW,
        records_root=settings.projects_root,
        daily_plans_root=settings.daily_plans_root,
    )
    committer = SessionCommitterLocal(
        file_store=file_store,
        decision_log_store=DecisionLogStoreJson(runtime_root, vault_key),
        session_store=SessionStoreJson(runtime_root),
        suggestions_repository=SuggestionsRepositoryJson(runtime_root, vault_key, lambda: NOW),
        cursor_store=cursors,
    )
    reader = VaultReaderMarkdown(settings, _Inbox(), cursors)
    context = PlanningContext(
        vault_root=vault_key,
        projects_prefix="1-projects",
        user_email=settings.user.email,
        initial_lookback_days=settings.initial_lookback_days,
    )
    return McpServer(PlanningTools(context, reader, committer, lambda: NOW, new_id, cursors), "test")


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


def test_full_planning_session_confirmed_writes_records_plan_and_logs_without_touching_vault_nyssa_ai(
    tmp_path: Path,
) -> None:
    vault_root = tmp_path / "vault"
    runtime_root = tmp_path / "runtime"
    vault_root.mkdir()
    runtime_root.mkdir()
    _vault(vault_root)
    server = _server(vault_root, runtime_root)

    with _captured_logs() as log_records:
        started = _run(
            server,
            '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}',
            _call(2, "daily_tasks_start_session"),
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
                        "record_kind": "task",
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
    assert not (vault_root / ".nyssa-ai").exists()
    blocker_text = (vault_root / f"{PROJECT}/blockers/b1-google-oauth-app-verification.md").read_text(encoding="utf-8")
    assert "blocker-state: resolved" in blocker_text or "state: resolved" in blocker_text
    plan = (vault_root / "2-areas/daily-plans/2026.11.03-daily-plan.md").read_text(encoding="utf-8")
    assert "Wire Gmail connector behind Communication-Port" in plan and "## Decisions" in plan
    decisions = json.loads((runtime_root / "decision-log.json").read_text(encoding="utf-8"))["entries"]
    assert [d["verdict"] for d in decisions] == ["accept", None]
    assert json.loads((runtime_root / "suggestions.json").read_text(encoding="utf-8"))["suggestions"] == []
    assert (
        json.loads((runtime_root / "fetch-cursors.json").read_text(encoding="utf-8"))["cursors"]["gmail"][
            "last_external_id"
        ]
        == "m1"
    )
    assert (runtime_root / "sessions/2026.11.03.json").exists()
    handled = [f for level, msg, f in log_records if msg.startswith("mcp request")]
    assert [f["status"] for f in handled][-1] == "ok" and handled[-1]["session_id"] == session_id


def test_full_planning_session_cancelled_writes_nothing(tmp_path: Path) -> None:
    vault_root = tmp_path / "vault"
    runtime_root = tmp_path / "runtime"
    vault_root.mkdir()
    runtime_root.mkdir()
    _vault(vault_root)
    before = sorted(p.relative_to(vault_root).as_posix() for p in vault_root.rglob("*"))
    server = _server(vault_root, runtime_root)

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
    assert sorted(p.relative_to(vault_root).as_posix() for p in vault_root.rglob("*")) == before
    assert not (vault_root / ".nyssa-ai").exists()


def test_full_planning_session_dispatcher_recovers_after_unconfirmed_attempt(tmp_path: Path) -> None:
    vault_root = tmp_path / "vault"
    runtime_root = tmp_path / "runtime"
    vault_root.mkdir()
    runtime_root.mkdir()
    _vault(vault_root)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "config.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "user": {"name": "Jordan", "email": "jordan@example.com"},
                "timezone": "America/Chicago",
            }
        ),
        encoding="utf-8",
    )
    numbers = count(1)
    resolver = VaultCollaboratorResolver(
        overrides=ServerOverrides(config_dir=config_dir, runtime_root=runtime_root),
        clock=lambda: NOW,
    )
    dispatcher = PlanningToolsDispatcher(
        resolver=resolver,
        clock=lambda: NOW,
        new_id=lambda: UUID(f"019a4b2c-9000-7000-8000-{next(numbers):012x}"),
    )
    server = McpServer(dispatcher, "test")

    started = _run(server, _call(1, "daily_tasks_start_session", date="2026-11-03", vault_root=str(vault_root)))
    session_id = str(_body(started[0])["session_id"])
    responses = _run(
        server,
        _call(2, "daily_tasks_advance_screen", session_id=session_id, target_screen=2),
        _call(
            3,
            "daily_tasks_execute_operations",
            session_id=session_id,
            original_words="plan gmail task today",
            operations=[
                {
                    "kind": "assign-to-day",
                    "row": 1,
                    "record_kind": "task",
                    "item_id": TASK_ID,
                    "local_date": "2026-11-03",
                }
            ],
        ),
        _call(4, "daily_tasks_advance_screen", session_id=session_id, target_screen=3),
        _call(5, "daily_tasks_confirm_plan", session_id=session_id, confirmed=False),
        _call(6, "daily_tasks_get_session_state", session_id=session_id),
        _call(7, "daily_tasks_confirm_plan", session_id=session_id, confirmed=True),
        _call(8, "daily_tasks_get_session_state", session_id=session_id),
    )

    assert [_body(r)["status"] for r in responses] == ["ok", "ok", "ok", "error", "ok", "ok", "error"]
    assert _body(responses[3])["code"] == "Forbidden"
    assert _body(responses[6])["code"] == "NotFound"
    assert not (vault_root / ".nyssa-ai").exists()
    plan = (vault_root / "2-areas/daily-plans/2026.11.03-daily-plan.md").read_text(encoding="utf-8")
    assert "Wire Gmail connector behind Communication-Port" in plan
