"""Responsibility: Hold one Markdown table cell with its links and ref ids.
Public interface:
`-- TableCell
    +-- links
    +-- refs
    `-- text

Table cell node read by `split_table_cells`.
"""

from dataclasses import dataclass

from daily_tasks.storage.cst.wiki_link import WikiLink


@dataclass(frozen=True, slots=True)
class TableCell:
    """Table cell text (trimmed, still escaped) with its wiki-links and `<!-- ref: ... -->` ids."""

    text: str
    links: tuple[WikiLink, ...]
    refs: tuple[str, ...]
