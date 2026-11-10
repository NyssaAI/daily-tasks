"""Responsibility: Describe why a Markdown record could not be parsed or changed.
Public interface:
`-- ParseError
    +-- code
    +-- detail
    +-- line
    `-- message

Structured parse failure returned in `Err` arms instead of raised.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ParseError:
    """Failure code, safe detail and the 1-based line it concerns, when known."""

    code: str
    detail: str
    line: int | None = None

    @property
    def message(self) -> str:
        """Human-readable summary including the line number."""
        return self.detail if self.line is None else f"line {self.line}: {self.detail}"
