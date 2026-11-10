"""Responsibility: Format a calendar day the way planning screens show it.
Public interface:
`-- format_day(day)

Screen dates use `YYYY.MM.DD`; a missing date renders as an em dash.
"""

from datetime import date


def format_day(day: date | None) -> str:
    """Return `YYYY.MM.DD`, or `—` when `day` is None."""
    return "—" if day is None else day.strftime("%Y.%m.%d")
