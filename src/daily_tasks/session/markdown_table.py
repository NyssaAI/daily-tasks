"""Responsibility: Render one Markdown table from header and row cells.
Public interface:
`-- markdown_table(headers, rows)

Pipe characters inside cells are escaped so a cell never splits the table.
"""

from collections.abc import Sequence


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def markdown_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    """Return the table as lines joined by newlines, without a trailing newline."""
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(_cell(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)
