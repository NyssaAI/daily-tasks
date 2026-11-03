# Responsibility: Represent an immutable DecisionLog DTO.
# Public interface:
# `-- DecisionLog
#     +-- entries
#     `-- workspace_root
"""DecisionLog DTO."""

from pydantic.dataclasses import dataclass
from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.decision_log_entry import DecisionLogEntry
from daily_tasks.domain.spec_ref import SpecRef


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class DecisionLog:
    """Append-only decision log (`.nyssa-ai/daily-tasks/decision-log.json`)."""

    workspace_root: str
    entries: tuple[DecisionLogEntry | SpecRef, ...]

