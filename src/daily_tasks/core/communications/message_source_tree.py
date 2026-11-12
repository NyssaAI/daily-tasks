"""Responsibility: Represent an immutable MessageSourceTree DTO.
Public interface:
`-- MessageSourceTree
    +-- source
    `-- threads

MessageSourceTree DTO.
"""

from pydantic.dataclasses import dataclass

from daily_tasks.core.communications.message_thread import MessageThread
from daily_tasks.core.records.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MessageSourceTree:
    """Threads grouped under their source."""

    source: str
    threads: tuple[MessageThread, ...]
