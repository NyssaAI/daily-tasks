# Responsibility: Represent an immutable MessageGraphContext DTO.
# Public interface:
# `-- MessageGraphContext
#     +-- built_at
#     +-- messages_root
#     +-- sources
#     +-- state_graph_hash
#     `-- status
"""MessageGraphContext DTO."""

from pydantic.dataclasses import dataclass
from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.utc_timestamp import UtcTimestamp
from daily_tasks.domain.message_source_status import MessageSourceStatus


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MessageGraphContext:
    """When and from what the message graph was built."""

    messages_root: str
    built_at: UtcTimestamp
    status: str
    state_graph_hash: str
    sources: tuple[MessageSourceStatus, ...]

