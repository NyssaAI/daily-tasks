"""Responsibility: Represent an immutable ItemType DTO.
Public interface:
`-- ItemType

ItemType DTO.
"""

from typing import Literal

type ItemType = Literal["task", "blocker"]
