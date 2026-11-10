"""Responsibility: Append one entry to the decisions section without touching unrelated bytes.
Public interface:
`-- append_decision(document, entry)

Surgical mutation: inserts whole new lines after the last entry of `## Decisions` or `## Decision Log`.
"""

from dataclasses import replace
from typing import Final

from nyssa_ai_result import Result, fail_error

from daily_tasks.storage.cst.line_ending import line_ending
from daily_tasks.storage.cst.markdown_document import MarkdownDocument
from daily_tasks.storage.cst.parse_error import ParseError
from daily_tasks.storage.cst.reparse_lines import reparse_lines
from daily_tasks.storage.cst.source_line import SourceLine

_DECISION_HEADINGS: Final = ("decisions", "decision log")


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
    return reparse_lines(lines)
