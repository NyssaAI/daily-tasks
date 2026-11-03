# Responsibility: Apply surgical edits to a parsed Markdown record without touching unrelated bytes.
# Public interface:
# +-- append_decision(document, entry)
# +-- set_checklist_mark(document, item_id, mark)
# `-- set_frontmatter_field(document, key, value)
"""Surgical mutations: each edit replaces only the targeted characters or inserts whole new lines."""

from dataclasses import replace

from nyssa_ai_result import Result, fail_error

from daily_tasks.storage.cst.nodes import MarkdownDocument, ScalarValue, SourceLine
from daily_tasks.storage.cst.parse_error import ParseError
from daily_tasks.storage.cst.parse_frontmatter import format_scalar
from daily_tasks.storage.cst.parser import parse_markdown
from daily_tasks.storage.cst.writer import line_ending, write_markdown

_DECISION_HEADINGS = ("decisions", "decision log")
_MARKS = frozenset(" x>-")


def _reparse(lines: list[SourceLine]) -> Result[MarkdownDocument, ParseError]:
    return parse_markdown(write_markdown(MarkdownDocument(tuple(lines), None, (), (), ())))


def set_checklist_mark(document: MarkdownDocument, item_id: str, mark: str) -> Result[MarkdownDocument, ParseError]:
    """Replace the one mark character of the checklist item with `<!-- id: item_id -->`.

    Fails with `invalid-checklist-mark` or `item-not-found`.
    """
    if mark not in _MARKS:
        return fail_error(ParseError("invalid-checklist-mark", f"unknown checklist mark {mark!r}"))
    item = next((i for i in document.checklist_items if i.item_id == item_id), None)
    if item is None:
        return fail_error(ParseError("item-not-found", f"no checklist item has id {item_id}"))
    lines = list(document.lines)
    old = lines[item.line_index]
    lines[item.line_index] = replace(old, text=old.text[: item.mark_column] + mark + old.text[item.mark_column + 1 :])
    return _reparse(lines)


def set_frontmatter_field(
    document: MarkdownDocument, key: str, value: ScalarValue
) -> Result[MarkdownDocument, ParseError]:
    """Replace the value of `key`, keeping its quoting style, or add `key` before the closing `---`.

    Fails with `missing-frontmatter` when the record has no frontmatter block.
    """
    frontmatter = document.frontmatter
    if frontmatter is None:
        return fail_error(ParseError("missing-frontmatter", "record has no frontmatter to update"))
    lines = list(document.lines)
    field = next((f for f in frontmatter.fields if f.key == key), None)
    if field is None:
        new_line = SourceLine(text=f"{key}: {format_scalar(value, quoted=True)}", ending=line_ending(document))
        lines.insert(frontmatter.close_index, new_line)
        return _reparse(lines)
    old = lines[field.line_index]
    is_quoted = field.raw_value.startswith('"') or (field.value is None and isinstance(value, str))
    start = field.value_column
    end = start + len(field.raw_value)
    lines[field.line_index] = replace(old, text=old.text[:start] + format_scalar(value, is_quoted) + old.text[end:])
    return _reparse(lines)


def append_decision(document: MarkdownDocument, entry: str) -> Result[MarkdownDocument, ParseError]:
    """Insert `entry` as a new line after the last non-blank line of `## Decisions` or `## Decision Log`.

    Fails with `section-not-found` when neither section exists.
    """
    section = next((s for s in document.sections if s.heading.title.casefold() in _DECISION_HEADINGS), None)
    if section is None:
        return fail_error(ParseError("section-not-found", "record has no Decisions or Decision Log section"))
    lines = list(document.lines)
    ending = line_ending(document)
    body = range(section.heading.line_index + 1, section.end_index)
    last = max((i for i in body if lines[i].text.strip()), default=None)
    if last is None:
        at = section.heading.line_index
        new_lines = [SourceLine("", ending), SourceLine(entry, ending)]
        if section.end_index == section.heading.line_index + 1 and section.end_index < len(lines):
            new_lines.append(SourceLine("", ending))
    else:
        at = last
        new_lines = [SourceLine(entry, ending)]
    if not lines[at].ending:
        lines[at] = replace(lines[at], ending=ending)
        new_lines[-1] = replace(new_lines[-1], ending="")
    lines[at + 1 : at + 1] = new_lines
    return _reparse(lines)
