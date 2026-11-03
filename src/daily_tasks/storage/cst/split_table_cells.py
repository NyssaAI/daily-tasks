# Responsibility: Split Markdown table cells and read their inline wiki-links and id/ref comments.
# Public interface:
# +-- extract_id(text)
# +-- extract_refs(text)
# +-- parse_wiki_links(text)
# +-- split_table_cells(line)
# `-- strip_comments(text)
"""Inline syntax readers shared by the CST parser and record parsers."""

import re
from typing import Final

from daily_tasks.storage.cst.nodes import TableCell, WikiLink

_ID: Final = re.compile(r"<!--\s*id:\s*(\S+)\s*-->")
_REF: Final = re.compile(r"<!--\s*ref:\s*(\S+)\s*-->")
_COMMENT: Final = re.compile(r"\s*<!--.*?-->")
_WIKI: Final = re.compile(r"\[\[([^\]|\\]+)(?:\\?\|([^\]]*))?\]\]")
_CELL_SPLIT: Final = re.compile(r"(?<!\\)\|")


def extract_id(text: str) -> str | None:
    """Return the `<!-- id: ... -->` value, if any."""
    found = _ID.search(text)
    return found.group(1) if found else None


def extract_refs(text: str) -> tuple[str, ...]:
    """Return every `<!-- ref: ... -->` value in order."""
    return tuple(_REF.findall(text))


def strip_comments(text: str) -> str:
    """Remove HTML comments and the whitespace before them."""
    return _COMMENT.sub("", text).strip()


def parse_wiki_links(text: str) -> tuple[WikiLink, ...]:
    """Return wiki-links, accepting both `[[a|b]]` and the table-escaped `[[a\\|b]]`."""
    return tuple(WikiLink(target=m.group(1), alias=m.group(2)) for m in _WIKI.finditer(text))


def split_table_cells(line: str) -> tuple[TableCell, ...] | None:
    """Split `| a | b |` into cells, or return None when the line is not a table row."""
    stripped = line.strip()
    if len(stripped) < 2 or not stripped.startswith("|") or not stripped.endswith("|"):
        return None
    parts = _CELL_SPLIT.split(stripped[1:-1])
    return tuple(TableCell(text=part.strip(), links=parse_wiki_links(part), refs=extract_refs(part)) for part in parts)
