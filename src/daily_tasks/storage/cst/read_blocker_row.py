# Responsibility: Read a daily plan blocker row back into its display view.
# Public interface:
# `-- read_blocker_row(row)
"""Inverse of the daily plan renderer's `| Blocker | Impact | Owner | Resolved When |` row."""

import re
from typing import Final

from daily_tasks.storage.cst.parse_error import ParseError
from daily_tasks.storage.cst.table_row import TableRow
from daily_tasks.storage.cst.types import PlanBlockerView

_BLOCKS: Final = re.compile(r"\s*Blocks (#\d+(?:, #\d+)*)\.$")


def _unescape(text: str) -> str:
    return text.replace("\\|", "|")


def read_blocker_row(row: TableRow) -> tuple[PlanBlockerView, tuple[int, ...]] | ParseError:
    """Blocker row `| Blocker | Impact | Owner | Resolved When |` and the plan row numbers it blocks."""
    cells = row.cells
    if len(cells) != 4 or not cells[0].links or not cells[0].refs:
        return ParseError("invalid-plan-row", "blocker row needs 4 cells and a linked blocker", row.line_index + 1)
    impact = _unescape(cells[1].text)
    blocks = _BLOCKS.search(impact)
    numbers = tuple(int(n) for n in re.findall(r"#(\d+)", blocks.group(1))) if blocks else ()
    link = cells[0].links[0]
    view = PlanBlockerView(
        blocker_id=cells[0].refs[0],
        title=_unescape(link.alias or link.target),
        path=link.target,
        impact=impact[: blocks.start()] if blocks else impact,
        owner=_unescape(cells[2].text),
        resolved_when=_unescape(cells[3].text),
    )
    return view, numbers
