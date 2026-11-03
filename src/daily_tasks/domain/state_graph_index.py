# Responsibility: Represent an immutable StateGraphIndex DTO.
# Public interface:
# `-- StateGraphIndex
#     +-- blocked_by
#     +-- blocks
#     +-- by_path
#     +-- by_person
#     +-- depends_on
#     +-- file_hashes
#     +-- origin_by_record
#     +-- parent
#     +-- project_order
#     +-- required_by
#     +-- threads
#     `-- title_terms
"""StateGraphIndex DTO."""

from collections.abc import Mapping
from pydantic import UUID7
from pydantic.dataclasses import dataclass
from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.person_index import PersonIndex
from daily_tasks.domain.record_origin import RecordOrigin


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class StateGraphIndex:
    """Relations and lookups between records."""

    project_order: tuple[UUID7, ...]
    parent: Mapping[UUID7, UUID7]
    depends_on: Mapping[UUID7, tuple[UUID7, ...]]
    required_by: Mapping[UUID7, tuple[UUID7, ...]]
    blocked_by: Mapping[UUID7, tuple[UUID7, ...]]
    blocks: Mapping[UUID7, tuple[UUID7, ...]]
    by_path: Mapping[str, UUID7]
    by_person: Mapping[str, PersonIndex]
    origin_by_record: Mapping[UUID7, RecordOrigin]
    title_terms: Mapping[str, tuple[UUID7, ...]]
    threads: Mapping[str, tuple[UUID7, ...]]
    file_hashes: Mapping[str, str]

