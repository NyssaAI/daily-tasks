"""Responsibility: Represent an immutable MessageGraphDerived DTO.
Public interface:
`-- MessageGraphDerived
    +-- for_review
    +-- messages
    +-- summary
    `-- threads

MessageGraphDerived DTO.
"""

from collections.abc import Mapping

from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.for_review_message import ForReviewMessage
from daily_tasks.domain.message_facts import MessageFacts
from daily_tasks.domain.message_graph_summary import MessageGraphSummary
from daily_tasks.domain.thread_facts import ThreadFacts


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MessageGraphDerived:
    """Computed message and thread facts, the review queue and the summary."""

    messages: Mapping[str, MessageFacts]
    threads: Mapping[str, ThreadFacts]
    for_review: tuple[ForReviewMessage, ...]
    summary: MessageGraphSummary
