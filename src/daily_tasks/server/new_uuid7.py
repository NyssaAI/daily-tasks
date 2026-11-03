# Responsibility: Generate RFC 9562 version 7 UUIDs for session, decision and plan identifiers.
# Public interface:
# `-- new_uuid7(now_ms, random_bytes)
"""Time-ordered UUIDv7 without depending on `uuid.uuid7` (Python 3.14+)."""

import os
import time
from collections.abc import Callable
from uuid import UUID


def new_uuid7(now_ms: Callable[[], int] | None = None, random_bytes: Callable[[int], bytes] | None = None) -> UUID:
    """Return a UUIDv7 from the Unix time in milliseconds and 74 random bits."""
    millis = (now_ms or (lambda: time.time_ns() // 1_000_000))() & ((1 << 48) - 1)
    rand = int.from_bytes((random_bytes or os.urandom)(10), "big")
    value = (millis << 80) | (0x7 << 76) | ((rand >> 62) & 0xFFF) << 64 | (0b10 << 62) | (rand & ((1 << 62) - 1))
    return UUID(int=value)
