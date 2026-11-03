# Responsibility: Define the lossless concrete syntax tree nodes of a Markdown record.
# Public interface:
# +-- ChecklistItem
# |   +-- item_id
# |   +-- line_index
# |   +-- mark
# |   +-- mark_column
# |   `-- text
# +-- Frontmatter
# |   +-- close_index
# |   +-- fields
# |   `-- open_index
# +-- FrontmatterField
# |   +-- key
# |   +-- line_index
# |   +-- raw_value
# |   +-- value
# |   `-- value_column
# +-- Heading
# |   +-- level
# |   +-- line_index
# |   +-- ref
# |   `-- title
# +-- MarkdownDocument
# |   +-- checklist_items
# |   +-- frontmatter
# |   +-- lines
# |   +-- sections
# |   `-- table_rows
# +-- ScalarValue
# +-- Section
# |   +-- checklist_items
# |   +-- end_index
# |   +-- heading
# |   `-- table_rows
# +-- SourceLine
# |   +-- ending
# |   `-- text
# +-- TableCell
# |   +-- links
# |   +-- refs
# |   `-- text
# +-- TableRow
# |   +-- cells
# |   `-- line_index
# `-- WikiLink
#     +-- alias
#     `-- target
"""CST nodes: every source line is kept with its line ending so unedited bytes round-trip unchanged."""

from dataclasses import dataclass

type ScalarValue = str | int | bool | None | tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SourceLine:
    """One physical line without its terminator, plus the terminator (`\\n`, `\\r\\n`, `\\r` or `` at EOF)."""

    text: str
    ending: str


@dataclass(frozen=True, slots=True)
class WikiLink:
    """Obsidian wiki-link `[[target|alias]]` (written `[[target\\|alias]]` inside tables)."""

    target: str
    alias: str | None


@dataclass(frozen=True, slots=True)
class FrontmatterField:
    """Scalar YAML field; `value_column` is where `raw_value` starts on its line."""

    key: str
    raw_value: str
    value: ScalarValue
    line_index: int
    value_column: int


@dataclass(frozen=True, slots=True)
class Frontmatter:
    """YAML block between the `---` delimiter lines at `open_index` and `close_index`."""

    fields: tuple[FrontmatterField, ...]
    open_index: int
    close_index: int


@dataclass(frozen=True, slots=True)
class Heading:
    """ATX heading; `title` excludes the hashes and any trailing `<!-- ref: ... -->` comment."""

    level: int
    title: str
    ref: str | None
    line_index: int


@dataclass(frozen=True, slots=True)
class ChecklistItem:
    """`- [m] text <!-- id: ... -->` item; `mark_column` is the column of `m`."""

    mark: str
    text: str
    item_id: str | None
    line_index: int
    mark_column: int


@dataclass(frozen=True, slots=True)
class TableCell:
    """Table cell text (trimmed, still escaped) with its wiki-links and `<!-- ref: ... -->` ids."""

    text: str
    links: tuple[WikiLink, ...]
    refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TableRow:
    """Table body row; header and delimiter rows are not represented."""

    cells: tuple[TableCell, ...]
    line_index: int


@dataclass(frozen=True, slots=True)
class Section:
    """Heading and the lines it owns, up to the next heading of the same or a higher level."""

    heading: Heading
    end_index: int
    checklist_items: tuple[ChecklistItem, ...]
    table_rows: tuple[TableRow, ...]


@dataclass(frozen=True, slots=True)
class MarkdownDocument:
    """Lossless parse of one Markdown record."""

    lines: tuple[SourceLine, ...]
    frontmatter: Frontmatter | None
    sections: tuple[Section, ...]
    checklist_items: tuple[ChecklistItem, ...]
    table_rows: tuple[TableRow, ...]
