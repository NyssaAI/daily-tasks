# Responsibility: Assemble the MessageGraph from matched messages.
# Public interface:
# `-- build_message_graph(graph, matches, messages_root, built_at, sources)
"""Pure projection of pre-matched messages into the `message-graph.json` shape."""

from collections.abc import Sequence
from datetime import datetime
from typing import Final
from uuid import UUID

from pydantic import TypeAdapter

from daily_tasks.domain import (
    ForReviewMessage,
    Message,
    MessageFacts,
    MessageGraph,
    MessageGraphContext,
    MessageGraphDerived,
    MessageGraphIndex,
    MessageGraphRecord,
    MessageGraphSummary,
    MessageLink,
    MessageSourceStatus,
    MessageSourceTree,
    MessageThread,
    StateGraph,
    ThreadFacts,
)
from daily_tasks.matching.types import MessageMatch

# The pydantic mypy plugin types aliased fields (`from`, `$ref`) by alias, so these DTOs are built by validation.
_RECORD: Final[TypeAdapter[MessageGraphRecord]] = TypeAdapter(MessageGraphRecord)
_FOR_REVIEW: Final[TypeAdapter[ForReviewMessage]] = TypeAdapter(ForReviewMessage)


def _location(message: Message) -> str:
    day = message.received_at.date().isoformat()
    return f"{day}/{message.source}/{message.external_id.replace(':', '-')}/message.json"


def _record(message: Message) -> MessageGraphRecord:
    return _RECORD.validate_python(
        {
            "source": message.source,
            "thread_id": message.thread_id,
            "received_at": message.received_at,
            "from": message.sender.address,
            "subject": message.subject,
            "channel": message.channel,
            "snippet": message.snippet,
            "attachment_ids": tuple(attachment.id for attachment in message.attachments),
            "location": _location(message),
        }
    )


def _attachment_labels(message: Message) -> tuple[str, ...]:
    return tuple(
        item.filename if item.status == "downloaded" else f"{item.filename} (not downloaded)"
        for item in message.attachments
    )


def _threads(matches: Sequence[MessageMatch]) -> dict[str, list[MessageMatch]]:
    threads: dict[str, list[MessageMatch]] = {}
    for match in sorted(matches, key=lambda item: (item.message.received_at, item.message.id)):
        threads.setdefault(match.message.thread_id, []).append(match)
    return threads


def _thread_facts(thread: Sequence[MessageMatch]) -> ThreadFacts:
    participants: list[str] = []
    linked: list[UUID] = []
    for match in thread:
        for address in (match.message.sender, *match.message.to, *match.message.cc):
            if address.address not in participants:
                participants.append(address.address)
        linked.extend(item.link.record_id for item in match.links if item.link.record_id not in linked)
    return ThreadFacts(
        participants=tuple(participants),
        last_activity=thread[-1].message.received_at,
        message_count=len(thread),
        linked_record_ids=tuple(linked),
    )


def build_message_graph(
    graph: StateGraph,
    matches: Sequence[MessageMatch],
    messages_root: str,
    built_at: datetime,
    sources: Sequence[MessageSourceStatus],
) -> MessageGraph:
    """Build a complete message graph for `matches`; the latest message of each thread needs review.

    `for_review` is ordered by `received_at`, then message id. Earlier messages of a thread are superseded
    by its latest message. Nothing is marked reviewed.
    """
    threads = _threads(matches)
    links: dict[str, tuple[MessageLink, ...]] = {}
    by_record: dict[UUID, list[str]] = {}
    by_sender: dict[str, list[str]] = {}
    facts: dict[str, MessageFacts] = {}
    for_review: list[ForReviewMessage] = []
    for thread in threads.values():
        latest = thread[-1].message.id
        for position, match in enumerate(thread):
            message = match.message
            by_sender.setdefault(message.sender.address, []).append(message.id)
            if match.links:
                links[message.id] = tuple(item.link for item in match.links)
            for item in match.links:
                by_record.setdefault(item.link.record_id, []).append(message.id)
            is_latest = message.id == latest
            facts[message.id] = MessageFacts(
                reviewed=False,
                linked=bool(match.links),
                latest_in_thread=is_latest,
                superseded_by=None if is_latest else latest,
                needs_review=is_latest,
            )
            if is_latest:
                for_review.append(
                    _FOR_REVIEW.validate_python(
                        {
                            "message_id": message.id,
                            "source": message.source,
                            "from": message.sender.address,
                            "subject": message.subject,
                            "snippet": message.snippet,
                            "received_at": message.received_at,
                            "earlier_in_thread": tuple(earlier.message.id for earlier in thread[:position]),
                            "attachments": _attachment_labels(message),
                            "links": {"$ref": f"#/index/links/{message.id}"} if match.links else (),
                        }
                    )
                )
    ordered = [match for thread in threads.values() for match in thread]
    linked_count = sum(1 for match in ordered if match.links)
    tree: dict[str, list[MessageThread]] = {}
    for thread_id, thread in threads.items():
        tree.setdefault(thread[0].message.source, []).append(
            MessageThread(thread_id=thread_id, message_ids=tuple(match.message.id for match in thread))
        )
    return MessageGraph(
        context=MessageGraphContext(
            messages_root=messages_root,
            built_at=built_at,
            status="complete",
            state_graph_hash=graph.context.inventory_hash,
            sources=tuple(sources),
        ),
        records={match.message.id: _record(match.message) for match in ordered},
        tree=tuple(MessageSourceTree(source=source, threads=tuple(items)) for source, items in tree.items()),
        index=MessageGraphIndex(
            thread={thread_id: tuple(match.message.id for match in thread) for thread_id, thread in threads.items()},
            by_sender={sender: tuple(ids) for sender, ids in by_sender.items()},
            links=links,
            by_record={record_id: tuple(ids) for record_id, ids in by_record.items()},
            attachments={item.id: match.message.id for match in ordered for item in match.message.attachments},
        ),
        derived=MessageGraphDerived(
            messages=facts,
            threads={thread_id: _thread_facts(thread) for thread_id, thread in threads.items()},
            for_review=tuple(sorted(for_review, key=lambda item: (item.received_at, item.message_id))),
            summary=MessageGraphSummary(
                fetched_this_run=len(ordered),
                unreviewed=len(ordered),
                needs_review=len(for_review),
                superseded=len(ordered) - len(for_review),
                linked=linked_count,
                unlinked=len(ordered) - linked_count,
                carried_from_earlier_days=0,
            ),
        ),
        diagnostics=(),
    )
