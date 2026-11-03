# Responsibility: Group the in-memory message graph snapshot DTOs.
# Public interface:
# +-- ForReviewMessage
# |   +-- attachments
# |   +-- earlier_in_thread
# |   +-- links
# |   +-- message_id
# |   +-- received_at
# |   +-- sender
# |   +-- snippet
# |   +-- source
# |   `-- subject
# +-- MessageFacts
# |   +-- carried_from
# |   +-- latest_in_thread
# |   +-- linked
# |   +-- needs_review
# |   +-- reviewed
# |   `-- superseded_by
# +-- MessageGraph
# |   +-- context
# |   +-- derived
# |   +-- diagnostics
# |   +-- index
# |   +-- note
# |   +-- records
# |   `-- tree
# +-- MessageGraphContext
# |   +-- built_at
# |   +-- messages_root
# |   +-- sources
# |   +-- state_graph_hash
# |   `-- status
# +-- MessageGraphDerived
# |   +-- for_review
# |   +-- messages
# |   +-- summary
# |   `-- threads
# +-- MessageGraphIndex
# |   +-- attachments
# |   +-- by_record
# |   +-- by_sender
# |   +-- links
# |   `-- thread
# +-- MessageGraphRecord
# |   +-- attachment_ids
# |   +-- channel
# |   +-- location
# |   +-- received_at
# |   +-- ref
# |   +-- sender
# |   +-- snippet
# |   +-- source
# |   +-- subject
# |   `-- thread_id
# +-- MessageGraphSummary
# |   +-- carried_from_earlier_days
# |   +-- fetched_this_run
# |   +-- linked
# |   +-- needs_review
# |   +-- superseded
# |   +-- unlinked
# |   `-- unreviewed
# +-- MessageLink
# |   +-- matched_text
# |   +-- reasons
# |   +-- record_id
# |   `-- record_type
# +-- MessageSourceStatus
# |   +-- error
# |   +-- fetched
# |   +-- name
# |   +-- since
# |   `-- status
# +-- MessageSourceTree
# |   +-- source
# |   `-- threads
# +-- MessageThread
# |   +-- message_ids
# |   `-- thread_id
# `-- ThreadFacts
#     +-- last_activity
#     +-- linked_record_ids
#     +-- message_count
#     `-- participants
"""MessageGraph layers: context, records, tree, index, derived facts and diagnostics."""

from collections.abc import Mapping
from datetime import date

from pydantic import MISSING, UUID7, Field
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.types import Diagnostic, SpecRef
from daily_tasks.domain.utc_timestamp import UtcTimestamp


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MessageSourceStatus:
    """Outcome of scanning one communication source for this graph."""

    name: str
    status: str
    since: UtcTimestamp
    fetched: int
    error: str | None


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MessageGraphContext:
    """When and from what the message graph was built."""

    messages_root: str
    built_at: UtcTimestamp
    status: str
    state_graph_hash: str
    sources: tuple[MessageSourceStatus, ...]


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MessageGraphRecord:
    """Message summary keyed by message id."""

    ref: str | MISSING = Field(default=MISSING, alias="$ref")
    source: str
    thread_id: str
    received_at: UtcTimestamp
    sender: str = Field(alias="from")
    subject: str | None
    channel: str | None | MISSING = MISSING
    snippet: str
    attachment_ids: tuple[str, ...]
    location: str


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MessageThread:
    """Messages of one thread, oldest first."""

    thread_id: str
    message_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MessageSourceTree:
    """Threads grouped under their source."""

    source: str
    threads: tuple[MessageThread, ...]


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MessageLink:
    """Pre-matched link from a message to a record, with the matching reasons."""

    record_type: str
    record_id: UUID7
    reasons: tuple[str, ...]
    matched_text: str


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MessageGraphIndex:
    """Lookups by thread, sender, linked record and attachment."""

    thread: Mapping[str, tuple[str, ...]]
    by_sender: Mapping[str, tuple[str, ...]]
    links: Mapping[str, tuple[MessageLink, ...]]
    by_record: Mapping[UUID7, tuple[str, ...]]
    attachments: Mapping[str, str]


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MessageFacts:
    """Computed review facts for one message."""

    reviewed: bool
    linked: bool
    latest_in_thread: bool
    superseded_by: str | None
    needs_review: bool
    carried_from: date | None | MISSING = MISSING


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class ThreadFacts:
    """Computed facts for one thread."""

    participants: tuple[str, ...]
    last_activity: UtcTimestamp
    message_count: int
    linked_record_ids: tuple[UUID7, ...]


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class ForReviewMessage:
    """Message handed to the agent for suggestion proposal."""

    message_id: str
    source: str
    sender: str = Field(alias="from")
    subject: str | None
    snippet: str
    received_at: UtcTimestamp
    earlier_in_thread: tuple[str, ...]
    attachments: tuple[str, ...]
    links: SpecRef | tuple[MessageLink, ...]


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MessageGraphSummary:
    """Headline message counts for this run."""

    fetched_this_run: int
    unreviewed: int
    needs_review: int
    superseded: int
    linked: int
    unlinked: int
    carried_from_earlier_days: int


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MessageGraphDerived:
    """Computed message and thread facts, the review queue and the summary."""

    messages: Mapping[str, MessageFacts]
    threads: Mapping[str, ThreadFacts]
    for_review: tuple[ForReviewMessage, ...]
    summary: MessageGraphSummary


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MessageGraph:
    """Point-in-time message graph, rebuilt from the message log and message files."""

    note: str | MISSING = Field(default=MISSING, alias="_note")
    context: MessageGraphContext
    records: Mapping[str, MessageGraphRecord]
    tree: tuple[MessageSourceTree, ...]
    index: MessageGraphIndex
    derived: MessageGraphDerived
    diagnostics: tuple[Diagnostic, ...]
