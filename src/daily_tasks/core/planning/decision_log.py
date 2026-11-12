"""Responsibility: Represent an immutable DecisionLog record.
Public interface:
`-- DecisionLog
    +-- entries
    `-- vault_root
"""

from pydantic.dataclasses import dataclass

from daily_tasks.core.planning.decision_log_entry import DecisionLogEntry
from daily_tasks.core.records.dto_config import DTO_CONFIG
from daily_tasks.core.records.spec_ref import SpecRef


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class DecisionLog:
    """Append-only decision log (`<runtime_root>/decision-log.json`)."""

    vault_root: str
    entries: tuple[DecisionLogEntry | SpecRef, ...]
