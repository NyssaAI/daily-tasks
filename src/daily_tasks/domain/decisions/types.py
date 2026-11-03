# Responsibility: Group the append-only decision log DTOs.
# Public interface:
# +-- DecisionLog
# |   +-- entries
# |   `-- workspace_root
# +-- DecisionLogEntry
# |   +-- action
# |   +-- after
# |   +-- before
# |   +-- corrects
# |   +-- decided_at
# |   +-- decided_by
# |   +-- decision
# |   +-- edits
# |   +-- id
# |   +-- operation_id
# |   +-- origin
# |   +-- original_words
# |   +-- question
# |   +-- record_ids
# |   +-- recorded_at
# |   +-- session_id
# |   +-- time_defaulted
# |   `-- verdict
# +-- DecisionOrigin
# +-- InstructionOrigin
# |   +-- kind
# |   +-- row
# |   `-- screen_id
# `-- SuggestionOrigin
#     +-- kind
#     +-- message_ids
#     +-- row
#     +-- screen_id
#     `-- suggestion_id
"""DecisionLog and DecisionLogEntry with the origin of each decision."""

from collections.abc import Mapping
from typing import Annotated, Literal

from pydantic import UUID7, Field, JsonValue
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.types import Actor, SpecRef
from daily_tasks.domain.utc_timestamp import UtcTimestamp


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class SuggestionOrigin:
    """Decision answering a numbered suggestion row."""

    kind: Literal["suggestion"]
    suggestion_id: UUID7
    screen_id: str
    row: int
    message_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class InstructionOrigin:
    """Decision given as a direct instruction on a numbered row."""

    kind: Literal["instruction"]
    screen_id: str
    row: int


type DecisionOrigin = Annotated[SuggestionOrigin | InstructionOrigin, Field(discriminator="kind")]


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class DecisionLogEntry:
    """One adjudicated decision with who decided, when, and the resulting change."""

    id: UUID7
    session_id: UUID7
    question: str
    decision: str
    decided_by: Actor
    decided_at: UtcTimestamp
    recorded_at: UtcTimestamp
    time_defaulted: bool
    original_words: str
    origin: DecisionOrigin
    verdict: Literal["accept", "edit", "reject"] | None
    edits: Mapping[str, JsonValue] | None
    action: str
    operation_id: UUID7 | None
    record_ids: tuple[UUID7, ...]
    before: Mapping[str, JsonValue] | None
    after: Mapping[str, JsonValue] | None
    corrects: UUID7 | None


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class DecisionLog:
    """Append-only decision log (`.nyssa-ai/daily-tasks/decision-log.json`)."""

    workspace_root: str
    entries: tuple[DecisionLogEntry | SpecRef, ...]
