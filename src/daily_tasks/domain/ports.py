# Responsibility: Represent an immutable Ports DTO.
# Public interface:
# `-- Ports
#     +-- communication
#     +-- daily_plan
#     +-- file_store
#     `-- project_plan
"""Ports DTO."""

from pydantic.dataclasses import dataclass

from daily_tasks.domain.communication_binding import CommunicationBinding
from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.file_store_binding import FileStoreBinding
from daily_tasks.domain.source_binding import SourceBinding


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class Ports:
    """Adapter bindings per port."""

    project_plan: tuple[SourceBinding, ...]
    daily_plan: tuple[SourceBinding, ...]
    communication: tuple[CommunicationBinding, ...]
    file_store: FileStoreBinding
