# Responsibility: Represent an immutable DodProgress DTO.
# Public interface:
# `-- DodProgress
#     +-- done
#     `-- total
"""DodProgress DTO."""

from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class DodProgress:
    """Checked and total Definition of Done items."""

    done: int
    total: int
