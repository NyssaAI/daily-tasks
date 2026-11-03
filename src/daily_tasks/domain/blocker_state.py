# Responsibility: Represent an immutable BlockerState DTO.
# Public interface:
# `-- BlockerState
"""BlockerState DTO."""

from typing import Literal

type BlockerState = Literal["open", "resolved"]
