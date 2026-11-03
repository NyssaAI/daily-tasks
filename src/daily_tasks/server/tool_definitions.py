# Responsibility: Describe the tools the MCP server lists, with their JSON input schemas.
# Public interface:
# +-- SECRET_TOOL_DEFINITIONS
# `-- TOOL_DEFINITIONS
"""MCP `tools/list` entries; argument names match `PlanningTools` and `SecretTools` method parameters."""

from typing import Final

from pydantic import JsonValue

_SESSION_ID: Final[dict[str, JsonValue]] = {"type": "string", "description": "session_id from start_session"}

TOOL_DEFINITIONS: Final[tuple[dict[str, JsonValue], ...]] = (
    {
        "name": "daily_tasks_start_session",
        "description": "Start today's planning session: read the vault, pre-match unread messages into pending "
        "suggestions and return screen 1 (plan the day). Writes nothing.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Local date YYYY-MM-DD; only today is accepted"},
                "focus": {"type": "string", "description": "Optional focus note shown on the plan"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "daily_tasks_get_session_state",
        "description": "Return the current screen of an active session without changing it.",
        "inputSchema": {
            "type": "object",
            "properties": {"session_id": _SESSION_ID},
            "required": ["session_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "daily_tasks_execute_operations",
        "description": "Apply the user's explicit replies: suggestion verdicts by row (accept/edit/reject) and "
        "operations (assign-to-day, unplan, set-status, reassign). All-or-nothing; staged until confirm.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": _SESSION_ID,
                "original_words": {"type": "string", "description": "The user's reply, verbatim"},
                "verdicts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "row": {"type": "integer"},
                            "verdict": {"enum": ["accept", "edit", "reject"]},
                            "edits": {"type": "object"},
                        },
                        "required": ["row", "verdict"],
                    },
                },
                "operations": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Operations as in docs/specs/operations.json",
                },
            },
            "required": ["session_id", "original_words"],
            "additionalProperties": False,
        },
    },
    {
        "name": "daily_tasks_advance_screen",
        "description": "Move forward: 2 shows the first or next project (assign days), 3 shows the plan recap.",
        "inputSchema": {
            "type": "object",
            "properties": {"session_id": _SESSION_ID, "target_screen": {"type": "integer", "enum": [2, 3]}},
            "required": ["session_id", "target_screen"],
            "additionalProperties": False,
        },
    },
    {
        "name": "daily_tasks_confirm_plan",
        "description": "After the user explicitly confirms the recap: apply staged record changes, write the "
        "daily plan, append the decision log and save cursors. Refused without confirmed=true.",
        "inputSchema": {
            "type": "object",
            "properties": {"session_id": _SESSION_ID, "confirmed": {"type": "boolean"}},
            "required": ["session_id", "confirmed"],
            "additionalProperties": False,
        },
    },
    {
        "name": "daily_tasks_cancel_session",
        "description": "Discard the session; nothing is written.",
        "inputSchema": {
            "type": "object",
            "properties": {"session_id": _SESSION_ID},
            "required": ["session_id"],
            "additionalProperties": False,
        },
    },
)

SECRET_TOOL_DEFINITIONS: Final[tuple[dict[str, JsonValue], ...]] = (
    {
        "name": "daily_tasks_capture_secret",
        "description": "Open a one-time local browser page where the user types a secret (vault token, Gmail "
        "client id/secret, Slack token) out-of-band. Waits for the user to submit it and returns only a receipt "
        "(namespace, key, provider, stored_at); the secret never reaches the agent. Never ask for it in chat.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "namespace": {"type": "string", "description": "Configuration namespace, e.g. communication"},
                "key": {"type": "string", "description": "Key within the namespace, e.g. gmail-client-secret"},
                "prompt_message": {"type": "string", "description": "Optional heading shown on the entry page"},
                "provider": {
                    "type": "string",
                    "description": "Optional preselected storage provider: aesLocal (default), literal or a vault",
                },
            },
            "required": ["namespace", "key"],
            "additionalProperties": False,
        },
    },
)
