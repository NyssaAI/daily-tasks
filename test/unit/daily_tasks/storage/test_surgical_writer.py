"""Responsibility: Verify surgical record edits change only their target bytes.
Public interface:
+-- DOD_ITEM
+-- DOD_TEXT
+-- test_append_decision_adds_one_line_after_existing_entries(newline)
+-- test_append_decision_empty_section_gets_first_entry(text, expected)
+-- test_append_decision_without_section_returns_error()
+-- test_set_checklist_mark_by_id_changes_only_the_mark(newline)
+-- test_set_checklist_mark_unknown_id_returns_item_not_found()
+-- test_set_checklist_mark_unknown_mark_returns_invalid_mark()
+-- test_set_frontmatter_field_keeps_trailing_comment()
+-- test_set_frontmatter_field_missing_key_is_added_before_closing_delimiter()
+-- test_set_frontmatter_field_without_frontmatter_returns_error()
+-- test_set_frontmatter_fields_changes_only_their_values(newline)
`-- test_write_markdown_unedited_text_with_mixed_endings_is_byte_identical()

Checklist toggles, frontmatter updates and decision appends on the task sample.
"""

import pytest
from nyssa_ai_result import Err, Ok

from conftest import SPECS_ROOT
from daily_tasks.storage.cst import (
    append_decision,
    parse_markdown,
    set_checklist_mark,
    set_frontmatter_field,
    write_markdown,
)

DOD_ITEM = "019a4b2c-1f00-7a10-8000-0000000000d5"
DOD_TEXT = "Unit tests verify email parsing and error handling for dropped connections"


def _task_text(newline: str = "\n") -> str:
    return (SPECS_ROOT / "4-sample-task.md").read_text(encoding="utf-8").replace("\n", newline)


def _changed_lines(before: str, after: str) -> list[tuple[str, str]]:
    old, new = before.splitlines(keepends=True), after.splitlines(keepends=True)
    assert len(old) == len(new)
    return [(a, b) for a, b in zip(old, new, strict=True) if a != b]


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_set_checklist_mark_by_id_changes_only_the_mark(newline: str) -> None:
    text = _task_text(newline)
    document = parse_markdown(text).unwrap()

    result = set_checklist_mark(document, DOD_ITEM, "x")

    assert isinstance(result, Ok)
    changed = _changed_lines(text, write_markdown(result.value))
    assert changed == [
        (
            f"- [ ] {DOD_TEXT} <!-- id: {DOD_ITEM} -->{newline}",
            f"- [x] {DOD_TEXT} <!-- id: {DOD_ITEM} -->{newline}",
        )
    ]


def test_set_checklist_mark_unknown_id_returns_item_not_found() -> None:
    document = parse_markdown(_task_text()).unwrap()

    result = set_checklist_mark(document, "019a4b2c-1f00-7a10-8000-0000000000ff", "x")

    assert isinstance(result, Err)
    assert result.error.code == "item-not-found"


def test_set_checklist_mark_unknown_mark_returns_invalid_mark() -> None:
    document = parse_markdown(_task_text()).unwrap()

    result = set_checklist_mark(document, DOD_ITEM, "?")

    assert isinstance(result, Err)
    assert result.error.code == "invalid-checklist-mark"


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_set_frontmatter_fields_changes_only_their_values(newline: str) -> None:
    text = _task_text(newline)
    document = parse_markdown(text).unwrap()

    result = (
        set_frontmatter_field(document, "task-state", "completed")
        .then(lambda d: set_frontmatter_field(d, "updated_at", "2026-11-04T09:00:00Z"))
        .then(lambda d: set_frontmatter_field(d, "resolved_at", "2026-11-04T09:00:00Z"))
    )

    assert isinstance(result, Ok)
    assert _changed_lines(text, write_markdown(result.value)) == [
        (f"task-state: in-progress{newline}", f"task-state: completed{newline}"),
        (f'updated_at: "2026-11-03T14:20:05Z"{newline}', f'updated_at: "2026-11-04T09:00:00Z"{newline}'),
        (f"resolved_at: null{newline}", f'resolved_at: "2026-11-04T09:00:00Z"{newline}'),
    ]


def test_set_frontmatter_field_keeps_trailing_comment() -> None:
    text = "---\nid: x\ntask-state: in-progress  # set by planner\n---\n# T\n"
    document = parse_markdown(text).unwrap()

    result = set_frontmatter_field(document, "task-state", "completed")

    assert isinstance(result, Ok)
    assert write_markdown(result.value) == "---\nid: x\ntask-state: completed  # set by planner\n---\n# T\n"


def test_set_frontmatter_field_missing_key_is_added_before_closing_delimiter() -> None:
    document = parse_markdown("---\nid: x\n---\n# T\n").unwrap()

    result = set_frontmatter_field(document, "resolved_at", "2026-11-04T09:00:00Z")

    assert isinstance(result, Ok)
    assert write_markdown(result.value) == '---\nid: x\nresolved_at: "2026-11-04T09:00:00Z"\n---\n# T\n'


def test_set_frontmatter_field_without_frontmatter_returns_error() -> None:
    document = parse_markdown("# T\n").unwrap()

    result = set_frontmatter_field(document, "task-state", "completed")

    assert isinstance(result, Err)
    assert result.error.code == "missing-frontmatter"


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_append_decision_adds_one_line_after_existing_entries(newline: str) -> None:
    text = newline.join(["# Plan", "", "## Decisions", "", "- first", "", "## Notes and references"]) + newline
    document = parse_markdown(text).unwrap()

    result = append_decision(document, "- second")

    assert isinstance(result, Ok)
    expected = newline.join(["# Plan", "", "## Decisions", "", "- first", "- second", "", "## Notes and references"])
    expected += newline
    assert write_markdown(result.value) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("## Decision Log\n\n## Notes\n", "## Decision Log\n\n- entry\n\n## Notes\n"),
        ("## Decisions\n## Notes\n", "## Decisions\n\n- entry\n\n## Notes\n"),
        ("## Decisions", "## Decisions\n\n- entry"),
    ],
)
def test_append_decision_empty_section_gets_first_entry(text: str, expected: str) -> None:
    document = parse_markdown(text).unwrap()

    result = append_decision(document, "- entry")

    assert isinstance(result, Ok)
    assert write_markdown(result.value) == expected


def test_append_decision_without_section_returns_error() -> None:
    document = parse_markdown(_task_text()).unwrap()

    result = append_decision(document, "- entry")

    assert isinstance(result, Err)
    assert result.error.code == "section-not-found"


def test_write_markdown_unedited_text_with_mixed_endings_is_byte_identical() -> None:
    text = "---\r\nid: x\n---\r\n# T  \n\n- [ ] a <!-- id: 1 -->\r\nno newline at end   "

    document = parse_markdown(text).unwrap()

    assert write_markdown(document) == text
