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

from daily_tasks.core.communications.for_review_message import ForReviewMessage
from daily_tasks.core.communications.message_facts import MessageFacts
from daily_tasks.core.communications.message_graph_summary import MessageGraphSummary
from daily_tasks.core.communications.thread_facts import ThreadFacts
from daily_tasks.core.records.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MessageGraphDerived:
    """Computed message and thread facts, the review queue and the summary."""

    messages: Mapping[str, MessageFacts]
    threads: Mapping[str, ThreadFacts]
    for_review: tuple[ForReviewMessage, ...]
    summary: MessageGraphSummary
