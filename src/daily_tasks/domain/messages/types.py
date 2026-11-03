# Responsibility: Group the persisted message, message log and fetch cursor DTOs.
# Public interface:
# +-- Attachment
# |   +-- downloaded_at
# |   +-- filename
# |   +-- id
# |   +-- mime_type
# |   +-- path
# |   +-- sha256
# |   +-- size_bytes
# |   `-- status
# +-- FetchCursor
# |   +-- last_error
# |   +-- last_external_id
# |   +-- last_run_at
# |   +-- last_status
# |   `-- since
# +-- FetchCursors
# |   +-- cursors
# |   `-- workspace_root
# +-- Message
# |   +-- attachments
# |   +-- body
# |   +-- body_format
# |   +-- cc
# |   +-- channel
# |   +-- external_id
# |   +-- fetched_at
# |   +-- id
# |   +-- received_at
# |   +-- sender
# |   +-- snippet
# |   +-- source
# |   +-- subject
# |   +-- thread_id
# |   +-- to
# |   `-- url
# +-- MessageAddress
# |   +-- address
# |   `-- name
# +-- MessageLog
# |   +-- entries
# |   `-- messages_root
# `-- MessageLogEntry
#     +-- day
#     +-- location
#     +-- message_id
#     +-- reviewed
#     `-- reviewed_at
"""Fetched Message records, the message log and per-source fetch cursors."""

from collections.abc import Mapping
from datetime import date

from pydantic import Field
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.utc_timestamp import UtcTimestamp


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MessageAddress:
    """Sender or recipient of a message."""

    name: str | None
    address: str


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class Attachment:
    """Message attachment and its download outcome."""

    id: str
    filename: str
    mime_type: str
    size_bytes: int
    sha256: str | None
    path: str | None
    downloaded_at: UtcTimestamp | None
    status: str


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class Message:
    """Fetched message (`<messages_root>/YYYY-MM-DD/<source>/<id>/message.json`)."""

    id: str
    source: str
    external_id: str
    thread_id: str
    received_at: UtcTimestamp
    sender: MessageAddress = Field(alias="from")
    to: tuple[MessageAddress, ...]
    cc: tuple[MessageAddress, ...]
    channel: str | None
    subject: str | None
    snippet: str
    body: str
    body_format: str
    attachments: tuple[Attachment, ...]
    url: str | None
    fetched_at: UtcTimestamp


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MessageLogEntry:
    """Where a fetched message is stored and whether it was reviewed."""

    day: date
    message_id: str
    location: str
    reviewed: bool
    reviewed_at: UtcTimestamp | None


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MessageLog:
    """Message log (`<messages_root>/message-log.json`)."""

    messages_root: str
    entries: tuple[MessageLogEntry, ...]


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class FetchCursor:
    """Fetch position and last outcome for one communication source."""

    since: UtcTimestamp
    last_external_id: str | None
    last_run_at: UtcTimestamp | None
    last_status: str
    last_error: str | None


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class FetchCursors:
    """Fetch cursors per source (`.nyssa-ai/daily-tasks/fetch-cursors.json`)."""

    workspace_root: str
    cursors: Mapping[str, FetchCursor]
