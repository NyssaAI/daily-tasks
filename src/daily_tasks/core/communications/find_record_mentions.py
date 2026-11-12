"""Responsibility: Find tasks and blockers a message mentions by record id, wiki link, or title.
Public interface:
`-- find_record_mentions(graph, message)
"""

import re
from collections.abc import Iterator
from typing import Final
from uuid import UUID

from daily_tasks.core.communications.communication_message import CommunicationMessage
from daily_tasks.core.communications.normalize_text import normalize_text
from daily_tasks.core.records.state_graph import StateGraph

_UUID7: Final[re.Pattern[str]] = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b", re.IGNORECASE
)
_WIKI_LINK: Final[re.Pattern[str]] = re.compile(r"\[\[([^\]|\\]+)(?:\\?\|([^\]]+))?\]\]")
_OPEN_STATES: Final[frozenset[str]] = frozenset({"not-started", "in-progress", "open"})


def _stem(path: str) -> str:
    return path.replace("\\", "/").rsplit("/", 1)[-1].removesuffix(".md").casefold()


def _titles(graph: StateGraph) -> Iterator[tuple[UUID, str, str]]:
    for record_id, task in graph.records.tasks.items():
        yield record_id, task.title, task.state
    for record_id, blocker in graph.records.blockers.items():
        yield record_id, blocker.title, blocker.state


def find_record_mentions(
    graph: StateGraph, message: CommunicationMessage
) -> Iterator[tuple[UUID, tuple[str, str, str]]]:
    """Yield `(record_id, (reason, matched_text, explanation))` for each mention, ids first."""
    text = "\n".join(part for part in (message.subject, message.body or message.snippet) if part)
    for found in _UUID7.finditer(text):
        record_id = UUID(found.group(0).lower())
        yield record_id, ("id-match", str(record_id), f"message cites record id {record_id}")
    stems = {_stem(path): record_id for path, record_id in graph.index.by_path.items()}
    titles = list(_titles(graph))
    for found in _WIKI_LINK.finditer(text):
        target, alias = found.group(1).strip(), (found.group(2) or "").strip()
        names = {normalize_text(target), normalize_text(alias)} - {""}
        for record_id, title, _ in titles:
            if normalize_text(title) in names:
                yield record_id, ("wiki-link", found.group(0), f"wiki link {found.group(0)} names '{title}'")
        if _stem(target) in stems:
            yield stems[_stem(target)], ("wiki-link", found.group(0), f"wiki link {found.group(0)} targets its file")
    padded = f" {normalize_text(text)} "
    for record_id, title, state in titles:
        normalized = normalize_text(title)
        if normalized and state in _OPEN_STATES and f" {normalized} " in padded:
            yield record_id, ("title-match", title, f"message mentions the title '{title}'")
