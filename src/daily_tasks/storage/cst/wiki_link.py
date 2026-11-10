"""Responsibility: Hold one Obsidian wiki-link target and alias.
Public interface:
`-- WikiLink
    +-- alias
    `-- target

Wiki-link node read from headings, sections and table cells.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WikiLink:
    """Obsidian wiki-link `[[target|alias]]` (written `[[target\\|alias]]` inside tables)."""

    target: str
    alias: str | None
