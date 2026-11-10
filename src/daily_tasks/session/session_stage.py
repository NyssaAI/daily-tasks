"""Responsibility: Name the lifecycle stages of a planning session.
Public interface:
`-- SessionStage
    +-- CANCELLED
    +-- CONFIRMED
    +-- INIT
    +-- SCREEN_1
    +-- SCREEN_2
    `-- SCREEN_3

Planning session stages: plan-the-day, assign-days, confirm, and the two terminal stages.
"""

from enum import StrEnum


class SessionStage(StrEnum):
    """Stage of a planning session; CONFIRMED and CANCELLED are terminal."""

    INIT = "init"
    SCREEN_1 = "screen-1"
    SCREEN_2 = "screen-2"
    SCREEN_3 = "screen-3"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
