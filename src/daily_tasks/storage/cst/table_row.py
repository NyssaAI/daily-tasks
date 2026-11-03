# Responsibility: Hold one Markdown table body row.
# Public interface:
# `-- TableRow
#     +-- cells
#     `-- line_index
"""Table row node; header and delimiter rows are skipped by the parser."""

from dataclasses import dataclass

from daily_tasks.storage.cst.table_cell import TableCell


@dataclass(frozen=True, slots=True)
class TableRow:
    """Table body row; header and delimiter rows are not represented."""

    cells: tuple[TableCell, ...]
    line_index: int
