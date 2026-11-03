# Responsibility: Define the lossless concrete syntax tree of a Markdown record.
# Public interface:
# `-- MarkdownDocument
#     +-- checklist_items
#     +-- frontmatter
#     +-- lines
#     +-- sections
#     `-- table_rows
"""CST root: every source line is kept with its line ending so unedited bytes round-trip unchanged."""

from dataclasses import dataclass

from daily_tasks.storage.cst.checklist_item import ChecklistItem
from daily_tasks.storage.cst.frontmatter import Frontmatter
from daily_tasks.storage.cst.section import Section
from daily_tasks.storage.cst.source_line import SourceLine
from daily_tasks.storage.cst.table_row import TableRow


@dataclass(frozen=True, slots=True)
class MarkdownDocument:
    """Lossless parse of one Markdown record."""

    lines: tuple[SourceLine, ...]
    frontmatter: Frontmatter | None
    sections: tuple[Section, ...]
    checklist_items: tuple[ChecklistItem, ...]
    table_rows: tuple[TableRow, ...]
