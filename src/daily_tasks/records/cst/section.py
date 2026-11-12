"""Responsibility: Hold a heading and the checklist items and table rows it owns.
Public interface:
`-- Section
    +-- checklist_items
    +-- end_index
    +-- heading
    `-- table_rows

Section node: a heading owns the lines up to the next heading of the same or a higher level.
"""

from dataclasses import dataclass

from daily_tasks.records.cst.checklist_item import ChecklistItem
from daily_tasks.records.cst.heading import Heading
from daily_tasks.records.cst.table_row import TableRow


@dataclass(frozen=True, slots=True)
class Section:
    """Heading and the lines it owns, up to the next heading of the same or a higher level."""

    heading: Heading
    end_index: int
    checklist_items: tuple[ChecklistItem, ...]
    table_rows: tuple[TableRow, ...]
