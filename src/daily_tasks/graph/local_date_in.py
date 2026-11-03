# Responsibility: Convert a UTC instant to the calendar date of a named timezone.
# Public interface:
# `-- local_date_in(instant, timezone)
"""Local calendar date of an aware instant in an IANA timezone."""

from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from nyssa_ai_result import Result, fail, ok


def local_date_in(instant: datetime, timezone: str) -> Result[date]:
    """Return the date at `instant` in `timezone`.

    Fails with `Validation` when `instant` is naive or `timezone` is not a known IANA name.
    """
    if instant.utcoffset() is None:
        return fail("Build time must be timezone-aware.", "Validation")
    try:
        zone = ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError) as error:
        return fail(f"Unknown timezone '{timezone}'.", "Validation", cause=error)
    return ok(instant.astimezone(zone).date())
