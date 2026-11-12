"""Responsibility: Convert between Slack `ts` strings and UTC datetimes without float rounding.
Public interface:
+-- slack_timestamp(value)
`-- slack_ts_from_datetime(value)

Slack `ts` values are `<epoch seconds>.<6-digit microseconds>` strings.
"""

from datetime import UTC, datetime, timedelta
from typing import Final

_EPOCH: Final = datetime(1970, 1, 1, tzinfo=UTC)


def slack_timestamp(value: str) -> datetime:
    """Return the UTC datetime of Slack `ts`; a malformed value raises `ValueError`."""
    seconds, _, fraction = value.partition(".")
    if not seconds.isdigit() or (fraction and not fraction.isdigit()):
        raise ValueError(f"invalid Slack ts '{value}'")
    micros = int((fraction + "000000")[:6])
    return _EPOCH + timedelta(seconds=int(seconds), microseconds=micros)


def slack_ts_from_datetime(value: datetime) -> str:
    """Return the Slack `ts` string of an aware datetime (used for the `oldest` query parameter)."""
    elapsed = value - _EPOCH
    seconds = elapsed // timedelta(seconds=1)
    micros = (elapsed - timedelta(seconds=seconds)) // timedelta(microseconds=1)
    return f"{seconds}.{micros:06d}"
