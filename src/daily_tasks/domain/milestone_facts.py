# Responsibility: Represent an immutable MilestoneFacts DTO.
# Public interface:
# `-- MilestoneFacts
#     +-- closable
#     +-- in_progress_plannable
#     +-- lowest_incomplete
#     +-- tasks_open
#     `-- tasks_total
"""MilestoneFacts DTO."""

from pydantic import MISSING
from pydantic.dataclasses import dataclass
from daily_tasks.domain.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MilestoneFacts:
    """Computed progress facts for a milestone."""

    lowest_incomplete: bool
    in_progress_plannable: bool | MISSING = MISSING
    tasks_open: int
    tasks_total: int
    closable: bool

