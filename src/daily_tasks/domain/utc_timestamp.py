# Responsibility: Parse ISO 8601 timestamps and require a UTC offset.
# Public interface:
# `-- UtcTimestamp
"""ISO 8601 timestamp type that only accepts UTC values (`Z` or `+00:00`)."""

from datetime import datetime, timedelta
from typing import Annotated

from pydantic import AfterValidator, AwareDatetime


def _require_utc(value: datetime) -> datetime:
    if value.utcoffset() != timedelta(0):
        raise ValueError("timestamp must be UTC")
    return value


type UtcTimestamp = Annotated[AwareDatetime, AfterValidator(_require_utc)]
