"""Responsibility: Define pure data types for communication batches and deterministic message matching.
Public interface:
+-- FetchBatch
|   +-- cursors
|   `-- messages
+-- MatchedLink
|   +-- confidence
|   +-- link
|   `-- reasoning
+-- MessageMatch
|   +-- links
|   +-- message
|   `-- signals
+-- Signal
|   +-- kind
|   +-- phrase
|   `-- quote
`-- SignalKind
"""

from dataclasses import dataclass
from typing import Literal

from daily_tasks.core.communications.communication_message import CommunicationMessage
from daily_tasks.core.communications.fetch_cursors import FetchCursors
from daily_tasks.core.communications.message_link import MessageLink

type SignalKind = Literal["completion", "blocked", "request"]


@dataclass(frozen=True, slots=True, kw_only=True)
class FetchBatch:
    """Fetched inbound messages paired with the advanced per-source cursors."""

    messages: tuple[CommunicationMessage, ...]
    cursors: FetchCursors


@dataclass(frozen=True, slots=True, kw_only=True)
class Signal:
    """Status or request phrase detected in a message, with its surrounding sentence."""

    kind: SignalKind
    phrase: str
    quote: str


@dataclass(frozen=True, slots=True, kw_only=True)
class MatchedLink:
    """Link from a message to a record with its confidence score (0..1) and explanation."""

    link: MessageLink
    confidence: float
    reasoning: str


@dataclass(frozen=True, slots=True, kw_only=True)
class MessageMatch:
    """One unprocessed message with its candidate record links and detected signals."""

    message: CommunicationMessage
    links: tuple[MatchedLink, ...]
    signals: tuple[Signal, ...]
