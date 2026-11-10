"""Responsibility: Represent an immutable MessageLog DTO.
Public interface:
`-- MessageLog
    +-- entries
    `-- messages_root

MessageLog DTO.
"""

from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.message_log_entry import MessageLogEntry


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MessageLog:
    """Message log (`<messages_root>/message-log.json`)."""

    messages_root: str
    entries: tuple[MessageLogEntry, ...]
