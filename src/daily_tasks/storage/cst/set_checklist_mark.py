"""Responsibility: Change the mark of one checklist item without touching unrelated bytes.
Public interface:
`-- set_checklist_mark(document, item_id, mark)

Surgical mutation: replaces only the one mark character of the targeted item.
"""

from dataclasses import replace
from typing import Final

from nyssa_ai_result import Result, fail_error

from daily_tasks.storage.cst.markdown_document import MarkdownDocument
from daily_tasks.storage.cst.parse_error import ParseError
from daily_tasks.storage.cst.reparse_lines import reparse_lines

_MARKS: Final = frozenset(" x>-")


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
    return reparse_lines(lines)
