# Responsibility: Group DTOs shared by several domain schemas.
# Public interface:
# +-- Actor
# |   +-- id
# |   `-- kind
# +-- Diagnostic
# |   +-- attachment_id
# |   +-- code
# |   +-- detail
# |   +-- level
# |   +-- path
# |   `-- source
# +-- DodItem
# |   +-- done
# |   +-- id
# |   `-- text
# +-- ItemType
# +-- PlanItem
# |   +-- item_id
# |   `-- item_type
# `-- SpecRef
#     `-- ref
"""Shared DTOs: spec references, actors, graph diagnostics, DoD items and planned items."""

from typing import Literal

from pydantic import MISSING, UUID7, Field
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG

type ItemType = Literal["task", "blocker"]


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class SpecRef:
    """Pointer (`{"$ref": ...}`) to another example document or JSON pointer."""

    ref: str = Field(alias="$ref")


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class Actor:
    """Person or agent identified by kind and id (an email for people)."""

    kind: str
    id: str


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class Diagnostic:
    """Graph build diagnostic with the optional subject it is about."""

    level: Literal["info", "warning", "error"]
    code: str
    detail: str
    source: str | MISSING = MISSING
    path: str | MISSING = MISSING
    attachment_id: str | MISSING = MISSING


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class DodItem:
    """Definition of Done checklist item with a stable id."""

    id: UUID7
    text: str
    done: bool


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class PlanItem:
    """Task or blocker selected for a day."""

    item_type: ItemType
    item_id: UUID7
