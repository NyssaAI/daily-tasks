"""Responsibility: Represent an immutable DecisionRef DTO.
Public interface:
`-- DecisionRef
    +-- id
    +-- question
    `-- resolution

DecisionRef DTO.
"""

from pydantic import UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class DecisionRef:
    """Decision taken during the planning session, as listed in the plan."""

    id: UUID7
    question: str
    resolution: str
