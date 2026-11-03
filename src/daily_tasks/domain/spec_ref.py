# Responsibility: Represent an immutable SpecRef DTO.
# Public interface:
# `-- SpecRef
#     `-- ref
"""SpecRef DTO."""

from pydantic import Field
from pydantic.dataclasses import dataclass
from daily_tasks.domain.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class SpecRef:
    """Pointer (`{"$ref": ...}`) to another example document or JSON pointer."""

    ref: str = Field(alias="$ref")

