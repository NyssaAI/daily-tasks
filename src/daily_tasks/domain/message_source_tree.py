"""Responsibility: Represent an immutable MessageSourceTree DTO.
Public interface:
`-- MessageSourceTree
    +-- source
    `-- threads

MessageSourceTree DTO.
"""

from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.message_thread import MessageThread


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MessageSourceTree:
    """Threads grouped under their source."""

    source: str
    threads: tuple[MessageThread, ...]
