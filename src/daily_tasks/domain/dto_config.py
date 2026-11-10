"""Responsibility: Define the shared Pydantic configuration for spec-parity DTOs.
Public interface:
`-- DTO_CONFIG

Shared configuration: unknown fields are rejected and JSON keys round-trip through aliases.
"""

from typing import Final

from pydantic import ConfigDict

DTO_CONFIG: Final[ConfigDict] = ConfigDict(
    extra="forbid",
    serialize_by_alias=True,
    validate_by_alias=True,
    validate_by_name=True,
)
