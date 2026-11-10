"""Responsibility: Read a daily plan task row back into its display view.
Public interface:
`-- read_item_row(row)

Inverse of the daily plan renderer's `| # | Status | Project | Milestone | Task | Due Date |` row.
"""

import re
from datetime import date
from typing import Final

from daily_tasks.storage.cst.parse_error import ParseError
from daily_tasks.storage.cst.table_cell import TableCell
from daily_tasks.storage.cst.table_row import TableRow
from daily_tasks.storage.cst.types import PlanItemView

_DATE: Final = re.compile(r"^(\d{4})\.(\d{2})\.(\d{2})$")
_DASH: Final = "—"


def _unescape(text: str) -> str:
    return text.replace("\\|", "|")


def _due(cell: TableCell) -> date | None:
    match = _DATE.match(cell.text)
    return date(int(match.group(1)), int(match.group(2)), int(match.group(3))) if match else None


def read_item_row(row: TableRow) -> tuple[PlanItemView, bool] | ParseError:
    """Task row `| # | Status | Project | Milestone | Task | Due Date |` and whether it is marked carried."""
    cells = row.cells
    if len(cells) != 6 or not cells[4].links or not cells[4].refs:
        return ParseError("invalid-plan-row", "task row needs 6 cells and a linked task", row.line_index + 1)
    link = cells[4].links[0]
    view = PlanItemView(
        item_id=cells[4].refs[0],
        title=_unescape(link.alias or link.target),
        path=link.target,
        project_title=_unescape(cells[2].text),
        milestone_title=None if cells[3].text == _DASH else _unescape(cells[3].text),
        status_mark=cells[1].text.strip("[]") or " ",
        due_date=_due(cells[5]),
    )
    return view, cells[4].text.startswith("↺")
