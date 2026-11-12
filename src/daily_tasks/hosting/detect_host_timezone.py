"""Responsibility: Detect and validate IANA timezone identifiers on the local host.
Public interface:
+-- detect_host_timezone()
`-- valid_iana_timezone(value)
"""

import os
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def valid_iana_timezone(value: str | None) -> bool:
    """Return True when `value` is a non-empty valid IANA timezone (never `'system'`)."""
    if not value or value.strip() == "system":
        return False
    try:
        ZoneInfo(value.strip())
    except (ZoneInfoNotFoundError, ValueError):
        return False
    return True


def detect_host_timezone() -> str | None:
    """Best-effort detection of the host IANA timezone from `TZ`, `/etc/localtime`, or `/etc/timezone`."""
    env_tz = os.environ.get("TZ", "").strip()
    if valid_iana_timezone(env_tz):
        return env_tz
    localtime = Path("/etc/localtime")
    if localtime.is_symlink():
        try:
            resolved = localtime.resolve().as_posix()
        except OSError:
            resolved = ""
        marker = "/zoneinfo/"
        if marker in resolved:
            candidate = resolved.split(marker, 1)[1]
            if valid_iana_timezone(candidate):
                return candidate
    etc_tz = Path("/etc/timezone")
    if etc_tz.is_file():
        try:
            candidate = etc_tz.read_text(encoding="utf-8").strip()
        except OSError:
            candidate = ""
        if valid_iana_timezone(candidate):
            return candidate
    return None
