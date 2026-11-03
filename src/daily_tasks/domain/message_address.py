# Responsibility: Represent an immutable MessageAddress DTO.
# Public interface:
# `-- MessageAddress
#     +-- address
#     `-- name
"""MessageAddress DTO."""

from pydantic.dataclasses import dataclass
from daily_tasks.domain.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MessageAddress:
    """Sender or recipient of a message."""

    name: str | None
    address: str

