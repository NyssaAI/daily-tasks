# Responsibility: Represent an immutable SuggestionOrigin DTO.
# Public interface:
# `-- SuggestionOrigin
#     +-- kind
#     +-- message_ids
#     +-- row
#     +-- screen_id
#     `-- suggestion_id
"""SuggestionOrigin DTO."""

from typing import Literal
from pydantic import UUID7
from pydantic.dataclasses import dataclass
from daily_tasks.domain.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class SuggestionOrigin:
    """Decision answering a numbered suggestion row."""

    kind: Literal["suggestion"]
    suggestion_id: UUID7
    screen_id: str
    row: int
    message_ids: tuple[str, ...]

