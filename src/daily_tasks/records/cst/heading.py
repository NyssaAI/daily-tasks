"""Responsibility: Hold one ATX heading of a Markdown record.
Public interface:
`-- Heading
    +-- level
    +-- line_index
    +-- ref
    `-- title

Heading node with its optional `<!-- ref: ... -->` id.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Heading:
    """ATX heading; `title` excludes the hashes and any trailing `<!-- ref: ... -->` comment."""

    level: int
    title: str
    ref: str | None
    line_index: int
