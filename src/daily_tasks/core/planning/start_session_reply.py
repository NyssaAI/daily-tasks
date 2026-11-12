"""Responsibility: Compose the message and payload `daily_tasks_start_session` returns with screen 1.
Public interface:
`-- start_session_reply(snapshot, harness_sources, pending)
"""

from collections.abc import Sequence

from pydantic import JsonValue

from daily_tasks.core.planning.types import VaultSnapshot


def start_session_reply(
    snapshot: VaultSnapshot, harness_sources: Sequence[str], pending: int
) -> tuple[str, dict[str, JsonValue]]:
    """Return the result message and payload; harness sources report `ok` because the host already read them."""
    sources: list[JsonValue] = [{"name": s.name, "status": s.status, "error": s.error} for s in snapshot.sources]
    sources.extend({"name": name, "status": "ok", "error": None} for name in harness_sources)
    malformed: list[JsonValue] = [
        {"path": m.path, "kind": m.kind, "code": m.code, "message": m.message} for m in snapshot.malformed_files
    ]
    message = f"Session started with {pending} pending suggestions."
    if snapshot.malformed_files:
        paths_preview = ", ".join(m.path for m in snapshot.malformed_files)
        count = len(snapshot.malformed_files)
        message += f" Notice: {count} malformed or unreadable file(s) were skipped: {paths_preview}."
    payload: dict[str, JsonValue] = {
        "pending_suggestions": pending,
        "message_sources": sources,
        "malformed_files": malformed,
    }
    return message, payload
