"""Responsibility: Correlate unprocessed messages with tasks and blockers through deterministic rules.
Public interface:
+-- LINK_CONFIDENCE
`-- match_messages(graph, messages, processed_ids)

Pure, deterministic message pre-matching: record ids, wiki links, titles, threads and assignees.
"""

from collections.abc import Collection, Iterable, Mapping, Sequence
from types import MappingProxyType
from typing import Final
from uuid import UUID

from daily_tasks.domain import Message, MessageLink, StateGraph
from daily_tasks.matching.detect_signals import detect_signals
from daily_tasks.matching.find_record_mentions import find_record_mentions
from daily_tasks.matching.types import MatchedLink, MessageMatch

LINK_CONFIDENCE: Final[Mapping[str, float]] = MappingProxyType(
    {
        "id-match": 1.0,
        "wiki-link": 0.9,
        "title-match": 0.7,
        "thread-seen-before": 0.6,
        "sender-is-assignee": 0.3,
    }
)

_CORROBORATION_BONUS: Final[float] = 0.05
_CLOSED_TASK_STATES: Final[frozenset[str]] = frozenset({"completed", "cancelled"})


type _Evidence = tuple[str, str, str]
"""Reason, matched text and explanation."""


def _record_type(graph: StateGraph, record_id: UUID) -> str | None:
    if record_id in graph.records.tasks:
        return "task"
    if record_id in graph.records.blockers:
        return "blocker"
    return None


def _assignee_evidence(graph: StateGraph, message: Message) -> Iterable[tuple[UUID, _Evidence]]:
    sender = message.sender.address.casefold()
    for record_id, task in graph.records.tasks.items():
        if task.assignee is not None and task.assignee.casefold() == sender and task.state not in _CLOSED_TASK_STATES:
            yield record_id, ("sender-is-assignee", sender, f"sender {sender} is the task assignee")


def _thread_evidence(graph: StateGraph, message: Message) -> Iterable[tuple[UUID, _Evidence]]:
    for record_id in graph.index.threads.get(message.thread_id, ()):
        explanation = f"thread {message.thread_id} was linked to this record before"
        yield record_id, ("thread-seen-before", message.thread_id, explanation)


def _text(message: Message) -> str:
    return "\n".join(part for part in (message.subject, message.body or message.snippet) if part)


def _score(reasons: Sequence[str]) -> float:
    strongest = max(LINK_CONFIDENCE[reason] for reason in reasons)
    return round(min(1.0, strongest + _CORROBORATION_BONUS * (len(reasons) - 1)), 2)


def _links(graph: StateGraph, message: Message) -> tuple[MatchedLink, ...]:
    gathered: dict[UUID, list[_Evidence]] = {}
    evidence = [*find_record_mentions(graph, message), *_thread_evidence(graph, message)]
    for record_id, found in [*evidence, *_assignee_evidence(graph, message)]:
        if _record_type(graph, record_id) is None:
            continue
        known = gathered.setdefault(record_id, [])
        if all(existing[0] != found[0] for existing in known):
            known.append(found)
    assignee_only = [rid for rid, items in gathered.items() if [e[0] for e in items] == ["sender-is-assignee"]]
    if len(assignee_only) > 1:
        for record_id in assignee_only:
            del gathered[record_id]
    links: list[MatchedLink] = []
    for record_id, items in gathered.items():
        ordered = sorted(items, key=lambda item: -LINK_CONFIDENCE[item[0]])
        reasons = tuple(item[0] for item in ordered)
        link = MessageLink(
            record_type=_record_type(graph, record_id) or "",
            record_id=record_id,
            reasons=reasons,
            matched_text=ordered[0][1],
        )
        reasoning = "; ".join(item[2] for item in ordered)
        links.append(MatchedLink(link=link, confidence=_score(reasons), reasoning=reasoning))
    return tuple(sorted(links, key=lambda item: (-item.confidence, item.link.record_type, str(item.link.record_id))))


def match_messages(
    graph: StateGraph, messages: Sequence[Message], processed_ids: Collection[str]
) -> tuple[MessageMatch, ...]:
    """Link each message not yet processed to the graph's tasks and blockers and flag its signal words.

    Messages whose id is in `processed_ids` (or repeated in `messages`) are dropped. Results are ordered by
    `received_at`, then message id. A link found only because the sender is the assignee is kept only when
    the sender is assigned exactly one open task; otherwise the assignee rule only corroborates other links.
    """
    seen: set[str] = set(processed_ids)
    fresh: list[Message] = []
    for message in sorted(messages, key=lambda item: (item.received_at, item.id)):
        if message.id not in seen:
            seen.add(message.id)
            fresh.append(message)
    return tuple(
        MessageMatch(
            message=message,
            links=_links(graph, message),
            signals=detect_signals(_text(message)),
        )
        for message in fresh
    )
