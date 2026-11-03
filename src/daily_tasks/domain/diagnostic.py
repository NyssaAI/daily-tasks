# Responsibility: Represent an immutable Diagnostic DTO.
# Public interface:
# `-- Diagnostic
#     +-- attachment_id
#     +-- code
#     +-- detail
#     +-- level
#     +-- path
#     `-- source
"""Diagnostic DTO."""

from typing import Literal
from pydantic import MISSING
from pydantic.dataclasses import dataclass
from daily_tasks.domain.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class Diagnostic:
    """Graph build diagnostic with the optional subject it is about."""

    level: Literal["info", "warning", "error"]
    code: str
    detail: str
    source: str | MISSING = MISSING
    path: str | MISSING = MISSING
    attachment_id: str | MISSING = MISSING

