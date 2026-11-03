# Responsibility: Define the pure data produced by deterministic message pre-matching.
# Public interface:
# +-- MatchedLink
# |   +-- confidence
# |   +-- link
# |   `-- reasoning
# +-- MessageMatch
# |   +-- links
# |   +-- message
# |   `-- signals
# +-- Signal
# |   +-- kind
# |   +-- phrase
# |   `-- quote
# `-- SignalKind
"""Matching results: scored links and detected signal phrases per message."""

from dataclasses import dataclass
from typing import Literal

from daily_tasks.domain import Message, MessageLink

type SignalKind = Literal["completion", "blocked", "request"]


@dataclass(frozen=True, slots=True, kw_only=True)
class Signal:
    """Status phrase found in a message, with the sentence it appears in."""

    kind: SignalKind
    phrase: str
    quote: str


@dataclass(frozen=True, slots=True, kw_only=True)
class MatchedLink:
    """Link from a message to a record with its confidence (0..1) and a readable explanation."""

    link: MessageLink
    confidence: float
    reasoning: str


@dataclass(frozen=True, slots=True, kw_only=True)
class MessageMatch:
    """One unprocessed message with its links (strongest first) and signals (in text order)."""

    message: Message
    links: tuple[MatchedLink, ...]
    signals: tuple[Signal, ...]
