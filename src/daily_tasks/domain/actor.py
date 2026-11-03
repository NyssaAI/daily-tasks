# Responsibility: Represent an immutable Actor DTO.
# Public interface:
# `-- Actor
#     +-- id
#     `-- kind
"""Actor DTO."""

from pydantic.dataclasses import dataclass
from daily_tasks.domain.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class Actor:
    """Person or agent identified by kind and id (an email for people)."""

    kind: str
    id: str

