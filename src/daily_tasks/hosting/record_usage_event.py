"""Responsibility: Extract opt-in telemetry settings and append usage events under runtime_root.
Public interface:
+-- USAGE_EVENTS_RELATIVE_PATH
+-- extract_telemetry_enabled(profile)
`-- record_usage_event(runtime_root, event, enabled)
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Final

from nyssa_ai_result import ErrorCategory, Result, fail, ok
from pydantic import JsonValue

USAGE_EVENTS_RELATIVE_PATH: Final = Path("usage") / "events.jsonl"


def extract_telemetry_enabled(profile: Mapping[str, JsonValue]) -> Result[bool]:
    """Read optional `telemetry.enabled` boolean from layered `config.json` (defaults to `False`)."""
    raw_telemetry = profile.get("telemetry")
    if raw_telemetry is None:
        return ok(False)
    if not isinstance(raw_telemetry, dict):
        return fail("telemetry in config.json must be a JSON object.", ErrorCategory.VALIDATION)
    raw_enabled = raw_telemetry.get("enabled", False)
    if not isinstance(raw_enabled, bool):
        return fail("telemetry.enabled in config.json must be a boolean.", ErrorCategory.VALIDATION)
    return ok(raw_enabled)


def record_usage_event(
    runtime_root: Path,
    event: Mapping[str, JsonValue],
    *,
    enabled: bool = False,
) -> Result[Path | None]:
    """Append a JSONL usage event to `<runtime_root>/usage/events.jsonl` only when `enabled` is True."""
    if not enabled:
        return ok(None)

    expanded = runtime_root.expanduser()
    if not expanded.is_absolute():
        return fail("runtime_root must be an absolute path.", ErrorCategory.VALIDATION)

    resolved_root = expanded.resolve()
    events_path = resolved_root / USAGE_EVENTS_RELATIVE_PATH
    usage_dir = events_path.parent
    if usage_dir.is_symlink() or events_path.is_symlink():
        return fail(
            f"Refusing to write usage telemetry through symlink at {events_path.as_posix()}.",
            ErrorCategory.VALIDATION,
        )

    try:
        dir_existed = usage_dir.exists()
        usage_dir.mkdir(parents=True, exist_ok=True)
        if not dir_existed and os.name == "posix":
            usage_dir.chmod(0o700)
        file_existed = events_path.exists()
        line = json.dumps(dict(event), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        with events_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(line)
        if not file_existed and os.name == "posix":
            events_path.chmod(0o600)
    except OSError as exc:
        return fail(f"Unable to append usage telemetry at {events_path.as_posix()}: {exc}", ErrorCategory.VALIDATION)
    return ok(events_path)
