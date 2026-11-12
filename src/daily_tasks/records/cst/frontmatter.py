"""Responsibility: Hold the YAML frontmatter block of a Markdown record.
Public interface:
`-- Frontmatter
    +-- close_index
    +-- fields
    `-- open_index

Frontmatter node: the fields between the opening and closing `---` lines.
"""

from dataclasses import dataclass

from daily_tasks.records.cst.frontmatter_field import FrontmatterField


@dataclass(frozen=True, slots=True)
class Frontmatter:
    """YAML block between the `---` delimiter lines at `open_index` and `close_index`."""

    fields: tuple[FrontmatterField, ...]
    open_index: int
    close_index: int
