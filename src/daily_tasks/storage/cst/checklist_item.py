"""Responsibility: Hold one Markdown checklist item and the column of its mark.
Public interface:
`-- ChecklistItem
    +-- item_id
    +-- line_index
    +-- mark
    +-- mark_column
    `-- text

Checklist item node: the mark column lets edits replace exactly one character.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ChecklistItem:
    """`- [m] text <!-- id: ... -->` item; `mark_column` is the column of `m`."""

    mark: str
    text: str
    item_id: str | None
    line_index: int
    mark_column: int
