"""Responsibility: Define the canonical record kind discriminator across Daily Tasks records.
Public interface:
`-- RecordKind
"""

from typing import Literal

type RecordKind = Literal["project", "milestone", "task", "blocker", "daily-plan"]
