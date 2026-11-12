"""Responsibility: Represent an immutable MessageGraphSummary DTO.
Public interface:
`-- MessageGraphSummary
    +-- carried_from_earlier_days
    +-- fetched_this_run
    +-- linked
    +-- needs_review
    +-- superseded
    +-- unlinked
    `-- unreviewed

MessageGraphSummary DTO.
"""

from pydantic.dataclasses import dataclass

from daily_tasks.core.records.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MessageGraphSummary:
    """Headline message counts for this run."""

    fetched_this_run: int
    unreviewed: int
    needs_review: int
    superseded: int
    linked: int
    unlinked: int
    carried_from_earlier_days: int
