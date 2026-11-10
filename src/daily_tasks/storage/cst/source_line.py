"""Responsibility: Hold one physical Markdown line and its own terminator.
Public interface:
`-- SourceLine
    +-- ending
    `-- text

Source line node: unedited bytes round-trip because every line keeps its terminator.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceLine:
    """One physical line without its terminator, plus the terminator (`\\n`, `\\r\\n`, `\\r` or `` at EOF)."""

    text: str
    ending: str
