# Responsibility: Split Markdown text into source lines that keep their own terminators.
# Public interface:
# `-- split_lines(text)
"""Line splitter underlying the lossless CST parser."""

import re
from typing import Final

from daily_tasks.storage.cst.source_line import SourceLine

_LINE: Final = re.compile(r"([^\r\n]*)(\r\n|\n|\r|$)")


def split_lines(text: str) -> tuple[SourceLine, ...]:
    """Split text into lines that keep their own terminator; joining them restores `text` exactly."""
    lines: list[SourceLine] = []
    position = 0
    while position < len(text):
        match = _LINE.match(text, position)
        if match is None:  # pragma: no cover - the pattern always matches
            break
        lines.append(SourceLine(text=match.group(1), ending=match.group(2)))
        position = match.end()
    return tuple(lines)
