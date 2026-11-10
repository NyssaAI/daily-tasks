"""Responsibility: Parse Markdown text into a lossless concrete syntax tree.
Public interface:
`-- parse_markdown(text)

Lossless CST parser for frontmatter, headings, checklist items and table rows.
"""

import re
from typing import Final

from nyssa_ai_result import Ok, Result, fail_error, ok

from daily_tasks.storage.cst.checklist_item import ChecklistItem
from daily_tasks.storage.cst.heading import Heading
from daily_tasks.storage.cst.markdown_document import MarkdownDocument
from daily_tasks.storage.cst.parse_error import ParseError
from daily_tasks.storage.cst.parse_frontmatter import parse_frontmatter
from daily_tasks.storage.cst.section import Section
from daily_tasks.storage.cst.split_lines import split_lines
from daily_tasks.storage.cst.split_table_cells import extract_id, extract_refs, split_table_cells, strip_comments
from daily_tasks.storage.cst.table_row import TableRow

_HEADING: Final = re.compile(r"^(#{1,6})[ \t]+(.*?)[ \t]*$")
_CHECKLIST: Final = re.compile(r"^[ \t]*[-*+][ \t]+\[(.)\][ \t]+(.*)$")
_TABLE_DELIMITER: Final = re.compile(r"^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
_FENCE: Final = re.compile(r"^[ \t]*(```|~~~)")
_MARKS: Final = frozenset(" x>-")


def _heading(text: str, index: int) -> Heading | None:
    match = _HEADING.match(text)
    if match is None:
        return None
    refs = extract_refs(match.group(2))
    return Heading(len(match.group(1)), strip_comments(match.group(2)), refs[0] if refs else None, index)


def _checklist(text: str, index: int) -> ChecklistItem | ParseError | None:
    match = _CHECKLIST.match(text)
    if match is None:
        return None
    if match.group(1) not in _MARKS:
        return ParseError("invalid-checklist-mark", f"unknown checklist mark {match.group(1)!r}", index + 1)
    return ChecklistItem(match.group(1), strip_comments(match.group(2)), extract_id(text), index, match.start(1))


def _sections(
    headings: list[Heading], items: list[ChecklistItem], rows: list[TableRow], count: int
) -> tuple[Section, ...]:
    sections: list[Section] = []
    for position, heading in enumerate(headings):
        end = next((h.line_index for h in headings[position + 1 :] if h.level <= heading.level), count)
        sections.append(
            Section(
                heading=heading,
                end_index=end,
                checklist_items=tuple(i for i in items if heading.line_index < i.line_index < end),
                table_rows=tuple(r for r in rows if heading.line_index < r.line_index < end),
            )
        )
    return tuple(sections)


def parse_markdown(text: str) -> Result[MarkdownDocument, ParseError]:
    """Parse a record; the document keeps every line so `write_markdown` reproduces `text` byte for byte.

    Fails with a frontmatter error code or `invalid-checklist-mark`.
    """
    lines = split_lines(text)
    frontmatter_result = parse_frontmatter(lines)
    if not isinstance(frontmatter_result, Ok):
        return frontmatter_result
    frontmatter = frontmatter_result.value
    headings: list[Heading] = []
    items: list[ChecklistItem] = []
    rows: list[TableRow] = []
    is_fenced = False
    is_table_header = False
    for index in range(frontmatter.close_index + 1 if frontmatter else 0, len(lines)):
        line = lines[index].text
        if _FENCE.match(line):
            is_fenced = not is_fenced
            continue
        if is_fenced:
            continue
        cells = split_table_cells(line)
        if cells is None:
            is_table_header = False
        elif _TABLE_DELIMITER.match(line.strip()):
            continue
        elif not is_table_header and (index + 1 < len(lines) and _TABLE_DELIMITER.match(lines[index + 1].text)):
            is_table_header = True
            continue
        else:
            rows.append(TableRow(cells=cells, line_index=index))
            continue
        heading = _heading(line, index)
        if heading is not None:
            headings.append(heading)
            continue
        item = _checklist(line, index)
        if isinstance(item, ParseError):
            return fail_error(item)
        if item is not None:
            items.append(item)
    return ok(
        MarkdownDocument(
            lines=lines,
            frontmatter=frontmatter,
            sections=_sections(headings, items, rows, len(lines)),
            checklist_items=tuple(items),
            table_rows=tuple(rows),
        )
    )
