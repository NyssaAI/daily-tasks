"""Responsibility: Represent an immutable MessageGraphIndex DTO.
Public interface:
`-- MessageGraphIndex
    +-- attachments
    +-- by_record
    +-- by_sender
    +-- links
    `-- thread

MessageGraphIndex DTO.
"""

from collections.abc import Mapping

from pydantic import UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.core.communications.message_link import MessageLink
from daily_tasks.core.records.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MessageGraphIndex:
    """Lookups by thread, sender, linked record and attachment."""

    thread: Mapping[str, tuple[str, ...]]
    by_sender: Mapping[str, tuple[str, ...]]
    links: Mapping[str, tuple[MessageLink, ...]]
    by_record: Mapping[UUID7, tuple[str, ...]]
    attachments: Mapping[str, str]
