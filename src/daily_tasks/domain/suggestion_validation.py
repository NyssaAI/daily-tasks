# Responsibility: Represent an immutable SuggestionValidation DTO.
# Public interface:
# `-- SuggestionValidation
#     +-- issues
#     `-- ok
"""SuggestionValidation DTO."""

from pydantic.dataclasses import dataclass
from daily_tasks.domain.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class SuggestionValidation:
    """Deterministic validation outcome of a suggestion."""

    ok: bool
    issues: tuple[str, ...]

