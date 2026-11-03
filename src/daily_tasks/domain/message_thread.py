# Responsibility: Represent an immutable MessageThread DTO.
# Public interface:
# `-- MessageThread
#     +-- message_ids
#     `-- thread_id
"""MessageThread DTO."""

from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MessageThread:
    """Messages of one thread, oldest first."""

    thread_id: str
    message_ids: tuple[str, ...]
