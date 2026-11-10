"""Responsibility: Represent an immutable WorkState DTO.
Public interface:
`-- WorkState

WorkState DTO.
"""

from typing import Literal

type WorkState = Literal["not-started", "in-progress", "completed", "cancelled"]
