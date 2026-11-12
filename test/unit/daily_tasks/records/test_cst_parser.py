"""Responsibility: Verify the lossless CST parser and the record parsers against canonical samples and `state:` keys.
Public interface:
+-- SAMPLES
+-- test_parse_blocker_sample_reads_resolution_and_blocked_records()
+-- test_parse_markdown_crlf_text_writes_back_byte_identical()
+-- test_parse_markdown_frontmatter_keeps_unknown_fields()
+-- test_parse_markdown_malformed_text_returns_parse_error(text, code, line)
+-- test_parse_markdown_sample_writes_back_byte_identical(name)
+-- test_parse_markdown_table_row_reads_escaped_wiki_link_and_ref()
+-- test_parse_markdown_task_sample_tracks_checklist_ids_and_lines()
+-- test_parse_milestone_sample_inherits_owner_and_reads_tasks()
+-- test_parse_project_sample_returns_project_record()
+-- test_parse_task_sample_returns_task_record()
+-- test_parse_task_without_owner_returns_invalid_record()
`-- test_parse_work_records_with_canonical_state_key_succeeds()

Parse sample Markdown fixtures into CST nodes and domain records (`Project`, `Milestone`, `Task`, `Blocker`).
"""

from uuid import UUID

import pytest
from nyssa_ai_result import Err, Ok

from conftest import SAMPLES_ROOT
from daily_tasks.core.records import RecordLocation
from daily_tasks.records.cst import (
    parse_blocker,
    parse_markdown,
    parse_milestone,
    parse_project,
    parse_task,
    write_markdown,
)

SAMPLES = [
    "4-sample-task.md",
    "5-sample-project-index.md",
    "6-sample-milestone.md",
    "7-sample-blocker.md",
    "8-sample-daily-plan.md",
]


def _sample(name: str) -> str:
    with (SAMPLES_ROOT / name).open(encoding="utf-8", newline="") as handle:
        return handle.read()


@pytest.mark.parametrize("name", SAMPLES)
def test_parse_markdown_sample_writes_back_byte_identical(name: str) -> None:
    text = _sample(name)

    result = parse_markdown(text)

    assert isinstance(result, Ok)
    assert write_markdown(result.value) == text


def test_parse_markdown_task_sample_tracks_checklist_ids_and_lines() -> None:
    result = parse_markdown(_sample("4-sample-task.md"))

    assert isinstance(result, Ok)
    items = result.value.checklist_items
    assert [(i.mark, i.item_id, i.line_index + 1) for i in items] == [
        ("x", "019a4b2c-1f00-7a10-8000-0000000000d3", 34),
        ("x", "019a4b2c-1f00-7a10-8000-0000000000d4", 35),
        (" ", "019a4b2c-1f00-7a10-8000-0000000000d5", 36),
    ]
    assert items[2].text == "Unit tests verify email parsing and error handling for dropped connections"


def test_parse_markdown_frontmatter_keeps_unknown_fields() -> None:
    result = parse_markdown(_sample("8-sample-daily-plan.md"))

    assert isinstance(result, Ok)
    frontmatter = result.value.frontmatter
    assert frontmatter is not None
    values = {field.key: field.value for field in frontmatter.fields}
    assert values["document-maturity"] == "reviewed"
    assert values["record_version"] == 2
    assert values["tags"] == ("plan", "daily")


def test_parse_markdown_table_row_reads_escaped_wiki_link_and_ref() -> None:
    result = parse_markdown(_sample("6-sample-milestone.md"))

    assert isinstance(result, Ok)
    first = result.value.table_rows[0]
    link = first.cells[1].links[0]
    assert (link.target, link.alias) == ("t1-wire-gmail-connector", "Wire Gmail connector")
    assert first.cells[1].refs == ("019a4b2c-1f00-7a10-8000-000000000003",)
    assert first.cells[2].text == "[>]"
    assert first.line_index + 1 == 33


def test_parse_markdown_crlf_text_writes_back_byte_identical() -> None:
    text = _sample("4-sample-task.md").replace("\n", "\r\n")

    result = parse_markdown(text)

    assert isinstance(result, Ok)
    assert write_markdown(result.value) == text


@pytest.mark.parametrize(
    ("text", "code", "line"),
    [
        ("---\nid: 1\n", "unclosed-frontmatter", 1),
        ('---\ntitle: "open\n---\n', "invalid-string", 2),
        ("---\n  nested: value\n---\n", "non-scalar-field", 2),
        ("---\nid: 1\nid: 2\n---\n", "duplicate-field", 3),
        ("# T\n\n- [?] odd mark\n", "invalid-checklist-mark", 3),
    ],
)
def test_parse_markdown_malformed_text_returns_parse_error(text: str, code: str, line: int) -> None:
    result = parse_markdown(text)

    assert isinstance(result, Err)
    assert (result.error.code, result.error.line) == (code, line)


def test_parse_task_sample_returns_task_record() -> None:
    document = parse_markdown(_sample("4-sample-task.md")).unwrap()
    location = RecordLocation(path="2026.10.20-x/m2-spike/t1-wire-gmail-connector.md", source="markdown-projects")

    result = parse_task(document, location)

    assert isinstance(result, Ok)
    task = result.value
    assert task.title == "Wire Gmail connector behind Communication-Port"
    assert task.number == 1
    assert task.state == "in-progress"
    assert task.assignee == "sarah@example.com"
    assert [(str(d.id)[-2:], d.done) for d in task.definition_of_done] == [("d3", True), ("d4", True), ("d5", False)]
    assert task.required_by == (UUID("019a4b2c-1f00-7a10-8000-000000000004"),)
    assert task.blocked_by == (UUID("019a4b2c-1f00-7a10-8000-000000000005"),)
    assert task.depends_on == ()


def test_parse_work_records_with_canonical_state_key_succeeds() -> None:
    task_text = _sample("4-sample-task.md").replace("task-state: in-progress", "state: in-progress")
    task_doc = parse_markdown(task_text).unwrap()
    task_res = parse_task(task_doc, RecordLocation(path="2026.10.20-x/m2/t1-wire.md", source="markdown-projects"))
    assert isinstance(task_res, Ok) and task_res.value.state == "in-progress"

    blocker_text = _sample("7-sample-blocker.md").replace("blocker-state: open", "state: open")
    blocker_doc = parse_markdown(blocker_text).unwrap()
    blocker_res = parse_blocker(
        blocker_doc,
        RecordLocation(path="2026.10.20-x/blockers/b1-oauth.md", source="markdown-projects", inherited_owner="j@x.com"),
    )
    assert isinstance(blocker_res, Ok) and blocker_res.value.state == "open"


def test_parse_project_sample_returns_project_record() -> None:
    document = parse_markdown(_sample("5-sample-project-index.md")).unwrap()
    location = RecordLocation(path="2026.10.20-daily-tasks-mcp-server/project-index.md", source="markdown-projects")

    result = parse_project(document, location)

    assert isinstance(result, Ok)
    project = result.value
    assert project.description == "Python MCP server that runs the plan-the-day session with pluggable ports."
    assert project.directory_date.isoformat() == "2026-10-20"
    assert [str(m)[-2:] for m in project.milestone_ids] == ["10", "02", "12", "21"]
    assert project.blocker_ids == (UUID("019a4b2c-1f00-7a10-8000-000000000005"),)


def test_parse_milestone_sample_inherits_owner_and_reads_tasks() -> None:
    document = parse_markdown(_sample("6-sample-milestone.md")).unwrap()
    location = RecordLocation(
        path="2026.10.20-x/m2-spike/m2-spike.md", source="markdown-projects", inherited_owner="jordan@example.com"
    )

    result = parse_milestone(document, location)

    assert isinstance(result, Ok)
    milestone = result.value
    assert (milestone.number, milestone.owner) == (2, "jordan@example.com")
    assert len(milestone.definition_of_done) == 3
    assert [str(t)[-2:] for t in milestone.task_ids] == ["03", "04", "07", "08"]
    assert milestone.blocked_by == (UUID("019a4b2c-1f00-7a10-8000-000000000005"),)


def test_parse_blocker_sample_reads_resolution_and_blocked_records() -> None:
    document = parse_markdown(_sample("7-sample-blocker.md")).unwrap()
    location = RecordLocation(
        path="2026.10.20-x/blockers/b1-oauth.md", source="markdown-projects", inherited_owner="jordan@example.com"
    )

    result = parse_blocker(document, location)

    assert isinstance(result, Ok)
    blocker = result.value
    assert (blocker.number, blocker.state) == (1, "open")
    assert blocker.impact.startswith("Google Cloud Console OAuth consent screen verification is pending")
    assert blocker.resolved_when.endswith("Production client credentials deployed to environment.")
    assert [str(b)[-2:] for b in blocker.blocks] == ["03", "02"]


def test_parse_task_without_owner_returns_invalid_record() -> None:
    text = (
        _sample("4-sample-task.md")
        .replace('owner: "jordan@example.com"\r\n', "")
        .replace('owner: "jordan@example.com"\n', "")
    )
    document = parse_markdown(text).unwrap()

    result = parse_task(document, RecordLocation(path="t1-x.md", source="markdown-projects"))

    assert isinstance(result, Err)
    assert result.error.code == "invalid-record"
    assert "owner" in result.error.detail
