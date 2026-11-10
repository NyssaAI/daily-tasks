"""Responsibility: Prove MarkdownFileStore writes only adjudicated changes, atomically and surgically.
Public interface:
+-- BLOCKER_PATH
+-- DOD_ITEM
+-- NOW
+-- TASK_PATH
+-- test_markdown_file_store_append_decisions_creates_missing_log(tmp_path)
+-- test_markdown_file_store_append_decisions_keeps_earlier_entries(tmp_path)
+-- test_markdown_file_store_blocker_state_uses_blocker_state_key(tmp_path)
+-- test_markdown_file_store_daily_plan_is_written_and_reparses(tmp_path, log_capture)
+-- test_markdown_file_store_hash_conflict_leaves_every_file_unchanged(tmp_path, log_capture)
+-- test_markdown_file_store_record_creation_is_unsupported(tmp_path)
+-- test_markdown_file_store_relative_workspace_root_is_rejected()
+-- test_markdown_file_store_session_and_suggestions_round_trip(tmp_path)
+-- test_markdown_file_store_status_change_rewrites_only_changed_values(tmp_path, newline, log_capture)
+-- test_markdown_file_store_unknown_dod_item_fails_without_writing(tmp_path)
+-- test_markdown_file_store_unreachable_record_fails(tmp_path, path, category)
`-- test_markdown_file_store_write_failure_returns_unavailable(tmp_path, log_capture)

Record changes, conflicts, daily plans and planning state files written under a temp workspace.
"""

import hashlib
from collections.abc import Mapping
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest
from nyssa_ai_result import Err, Ok
from pydantic import JsonValue, TypeAdapter

from conftest import SPECS_ROOT, LogCapture, load_spec
from daily_tasks.domain import DailyPlan, DecisionLog, DecisionLogEntry, PlanningSession, RecordChange, Suggestions
from daily_tasks.storage.cst import DailyPlanDocument, RecordLocation, parse_daily_plan, parse_markdown
from daily_tasks.storage.markdown_file_store import MarkdownFileStore

NOW = datetime(2026, 11, 3, 14, 20, 5, tzinfo=UTC)
TASK_PATH = "2026.10.20-daily-tasks-mcp-server/m2-planning-session-spike/t1-wire-gmail-connector.md"
BLOCKER_PATH = "2026.10.20-daily-tasks-mcp-server/blockers/b1-google-oauth-app-verification.md"
DOD_ITEM = "019a4b2c-1f00-7a10-8000-0000000000d5"
_CHANGE = TypeAdapter(RecordChange)


def _store(root: Path) -> MarkdownFileStore:
    return MarkdownFileStore(root, lambda: NOW)


def _seed(root: Path, relative: str, sample: str, newline: str = "\n") -> Path:
    text = (SPECS_ROOT / sample).read_text(encoding="utf-8").replace("\n", newline)
    path = root / "projects" / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
    return path


def _hash_of(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _change(path: str, expected_hash: str, after: Mapping[str, JsonValue], record_type: str = "task") -> RecordChange:
    raw = load_spec("record-change.json")
    assert isinstance(raw, dict)
    values = {**raw, "path": path, "expected_hash": expected_hash, "record_type": record_type, "after": after}
    return replace(_CHANGE.validate_python(values), status="pending", applied_at=None)


def _changed_lines(before: bytes, after: bytes) -> list[tuple[bytes, bytes]]:
    old, new = before.splitlines(keepends=True), after.splitlines(keepends=True)
    assert len(old) == len(new)
    return [(a, b) for a, b in zip(old, new, strict=True) if a != b]


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_markdown_file_store_status_change_rewrites_only_changed_values(
    tmp_path: Path, newline: str, log_capture: LogCapture
) -> None:
    task = _seed(tmp_path, TASK_PATH, "4-sample-task.md", newline)
    before = task.read_bytes()
    after: dict[str, JsonValue] = {"state": "completed", "updated_at": "2026-11-04T09:00:00Z", "dod": {DOD_ITEM: True}}

    result = _store(tmp_path).apply([_change(TASK_PATH, _hash_of(task), after)])

    assert isinstance(result, Ok)
    assert [(c.status, c.applied_at) for c in result.value] == [("applied", NOW)]
    nl = newline.encode()
    assert _changed_lines(before, task.read_bytes()) == [
        (b"task-state: in-progress" + nl, b"task-state: completed" + nl),
        (b'updated_at: "2026-11-03T14:20:05Z"' + nl, b'updated_at: "2026-11-04T09:00:00Z"' + nl),
        (
            b"- [ ] Unit tests verify email parsing and error handling for dropped connections <!-- id: "
            + DOD_ITEM.encode()
            + b" -->"
            + nl,
            b"- [x] Unit tests verify email parsing and error handling for dropped connections <!-- id: "
            + DOD_ITEM.encode()
            + b" -->"
            + nl,
        ),
    ]
    assert log_capture.operations[-1][:2] == ("info", "file_store.apply")
    assert log_capture.operations[-1][2]["changes"] == 1


def test_markdown_file_store_blocker_state_uses_blocker_state_key(tmp_path: Path) -> None:
    blocker = _seed(tmp_path, BLOCKER_PATH, "7-sample-blocker.md")
    change = _change(BLOCKER_PATH, _hash_of(blocker), {"state": "resolved"}, "blocker")

    result = _store(tmp_path).apply([change])

    assert isinstance(result, Ok)
    assert "blocker-state: resolved\n" in blocker.read_text(encoding="utf-8")


def test_markdown_file_store_hash_conflict_leaves_every_file_unchanged(
    tmp_path: Path, log_capture: LogCapture
) -> None:
    task = _seed(tmp_path, TASK_PATH, "4-sample-task.md")
    blocker = _seed(tmp_path, BLOCKER_PATH, "7-sample-blocker.md")
    originals = (task.read_bytes(), blocker.read_bytes())
    changes = [
        _change(TASK_PATH, _hash_of(task), {"state": "completed"}),
        _change(BLOCKER_PATH, "sha256:stale", {"state": "resolved"}, "blocker"),
    ]

    result = _store(tmp_path).apply(changes)

    assert isinstance(result, Err)
    assert result.category == "Conflict"
    assert (task.read_bytes(), blocker.read_bytes()) == originals
    assert log_capture.operations[-1][:2] == ("warn", "file_store.apply")
    assert log_capture.operations[-1][2]["path"] == BLOCKER_PATH


def test_markdown_file_store_unknown_dod_item_fails_without_writing(tmp_path: Path) -> None:
    task = _seed(tmp_path, TASK_PATH, "4-sample-task.md")
    original = task.read_bytes()
    change = _change(TASK_PATH, _hash_of(task), {"state": "completed", "dod": {"missing-id": True}})

    result = _store(tmp_path).apply([change])

    assert isinstance(result, Err)
    assert result.category == "Validation"
    assert task.read_bytes() == original


@pytest.mark.parametrize(("path", "category"), [("../outside.md", "Validation"), ("missing/t9-nothing.md", "NotFound")])
def test_markdown_file_store_unreachable_record_fails(tmp_path: Path, path: str, category: str) -> None:
    result = _store(tmp_path).apply([_change(path, "sha256:x", {"state": "completed"})])

    assert isinstance(result, Err)
    assert result.category == category


def test_markdown_file_store_record_creation_is_unsupported(tmp_path: Path) -> None:
    task = _seed(tmp_path, TASK_PATH, "4-sample-task.md")
    change = replace(_change(TASK_PATH, _hash_of(task), {"state": "not-started"}), before=None)

    result = _store(tmp_path).apply([change])

    assert isinstance(result, Err)
    assert result.category == "Validation"
    assert "in-place edits" in result.message


def test_markdown_file_store_daily_plan_is_written_and_reparses(tmp_path: Path, log_capture: LogCapture) -> None:
    plan = TypeAdapter(DailyPlan).validate_python(load_spec("daily-plan.json"))
    document = DailyPlanDocument(
        plan=plan,
        owner="jordan@example.com",
        tags=("daily-plan",),
        maturity="draft",
        record_version=2,
        items=(),
        blockers=(),
    )

    result = _store(tmp_path).write_daily_plan(document)

    assert result == Ok("daily-plans/2026.11.03-daily-plan.md")
    text = (tmp_path / "daily-plans" / "2026.11.03-daily-plan.md").read_text(encoding="utf-8")
    location = RecordLocation(path=result.value, source="markdown-daily-plans")
    reparsed = parse_daily_plan(parse_markdown(text).unwrap(), location, plan)
    assert isinstance(reparsed, Ok)
    assert reparsed.value.plan.local_date == plan.local_date
    assert log_capture.operations[-1][:2] == ("info", "file_store.write_daily_plan")


def test_markdown_file_store_append_decisions_keeps_earlier_entries(tmp_path: Path) -> None:
    store = _store(tmp_path)
    entry = TypeAdapter(DecisionLogEntry).validate_python(load_spec("decision-log-entry.json"))
    log_path = tmp_path / ".nyssa-ai" / "daily-tasks" / "decision-log.json"
    log_path.parent.mkdir(parents=True)
    log_path.write_text((SPECS_ROOT / "decision-log.json").read_text(encoding="utf-8"), encoding="utf-8")
    earlier = TypeAdapter(DecisionLog).validate_json(log_path.read_bytes()).entries
    second = replace(entry, id=UUID("019a4b2c-9000-7000-8000-0000000000e9"))

    assert isinstance(store.append_decisions([entry]), Ok)
    assert isinstance(store.append_decisions([second]), Ok)

    stored = TypeAdapter(DecisionLog).validate_json(log_path.read_bytes())
    assert stored.entries == (*earlier, entry, second)


def test_markdown_file_store_append_decisions_creates_missing_log(tmp_path: Path) -> None:
    entry = TypeAdapter(DecisionLogEntry).validate_python(load_spec("decision-log-entry.json"))

    result = _store(tmp_path).append_decisions([entry])

    assert isinstance(result, Ok)
    stored = TypeAdapter(DecisionLog).validate_json((tmp_path / ".nyssa-ai/daily-tasks/decision-log.json").read_bytes())
    assert stored == DecisionLog(workspace_root=tmp_path.as_posix(), entries=(entry,))


def test_markdown_file_store_session_and_suggestions_round_trip(tmp_path: Path) -> None:
    store = _store(tmp_path)
    session = TypeAdapter(PlanningSession).validate_python(load_spec("planning-session.json"))
    suggestions = TypeAdapter(Suggestions).validate_python(load_spec("suggestions.json"))

    assert isinstance(store.save_session(session), Ok)
    assert isinstance(store.save_suggestions(suggestions), Ok)

    state = tmp_path / ".nyssa-ai" / "daily-tasks"
    assert TypeAdapter(PlanningSession).validate_json((state / "sessions" / "2026.11.03.json").read_bytes()) == session
    assert TypeAdapter(Suggestions).validate_json((state / "suggestions.json").read_bytes()) == suggestions
    assert '"_note"' in (state / "sessions" / "2026.11.03.json").read_text(encoding="utf-8")


def test_markdown_file_store_write_failure_returns_unavailable(tmp_path: Path, log_capture: LogCapture) -> None:
    (tmp_path / "daily-plans").write_text("not a directory", encoding="utf-8")
    plan = TypeAdapter(DailyPlan).validate_python(load_spec("daily-plan.json"))
    document = DailyPlanDocument(
        plan=plan, owner="jordan@example.com", tags=(), maturity="draft", record_version=2, items=(), blockers=()
    )

    result = _store(tmp_path).write_daily_plan(document)

    assert isinstance(result, Err)
    assert result.category == "Unavailable"
    assert log_capture.operations[-1][:2] == ("error", "file_store.write_daily_plan")


def test_markdown_file_store_relative_workspace_root_is_rejected() -> None:
    with pytest.raises(ValueError, match="absolute"):
        MarkdownFileStore(Path("vault"), lambda: NOW)
