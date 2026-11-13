"""Responsibility: Describe the tools the MCP server lists, with their JSON input schemas.
Public interface:
+-- CONFIGURE_VAULT_TOOL
+-- SECRET_TOOL
+-- SECRET_TOOL_DEFINITIONS
+-- SETUP_STATUS_TOOL
+-- SETUP_TOOL_DEFINITIONS
`-- TOOL_DEFINITIONS
"""

from typing import Final

from pydantic import JsonValue

SECRET_TOOL: Final = "daily_tasks_capture_secret"
SETUP_STATUS_TOOL: Final = "daily_tasks_setup_status"
CONFIGURE_VAULT_TOOL: Final = "daily_tasks_configure_vault"

_SESSION_ID: Final[dict[str, JsonValue]] = {"type": "string", "description": "session_id from start_session"}
_VAULT_ROOT: Final[dict[str, JsonValue]] = {
    "type": "string",
    "description": "Optional absolute path to the vault root; defaults to bound CLI/environment or defaultVaultRoot",
}

TOOL_DEFINITIONS: Final[tuple[dict[str, JsonValue], ...]] = (
    {
        "name": "daily_tasks_start_session",
        "description": "Start today's planning session: read the vault, pre-match unread messages into pending "
        "suggestions and return screen 1 (plan the day). Writes nothing.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "vault_root": _VAULT_ROOT,
                "date": {"type": "string", "description": "Local date YYYY-MM-DD; only today is accepted"},
                "focus": {"type": "string", "description": "Optional focus note shown on the plan"},
                "messages": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Normalized unread messages read through the host's email/chat connection "
                    "(id, source, external_id, received_at, from, to, subject, snippet, body, fetched_at); "
                    "filtered against the source's fetch window",
                },
                "checked_sources": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Sources the host checked through its own connection, even with no new messages",
                },
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "daily_tasks_get_fetch_window",
        "description": "Return each source's next fetch window (since, after_epoch, last_external_id, "
        "has_cursor): the saved cursor, or the initial lookback (7 days by default) on a first pull. Read it "
        "before reading messages through an existing assistant connection. Writes nothing.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "vault_root": _VAULT_ROOT,
                "sources": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Source names (default: gmail, slack)",
                },
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
                    "description": "Staged planning operations (kind: assign-to-day, unplan, set-status, or reassign "
                    "with row/target fields and record_kind)",
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
        "name": SECRET_TOOL,
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

SETUP_TOOL_DEFINITIONS: Final[tuple[dict[str, JsonValue], ...]] = (
    {
        "name": SETUP_STATUS_TOOL,
        "description": "Inspect Daily Tasks setup gates read-only: user/repo Schema Version 2 config.json, "
        "vault layout, existing formatting templates, and communication source configuration. "
        "Call before Setup or when any gate fails. Writes nothing.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "vault_root": _VAULT_ROOT,
            },
            "additionalProperties": False,
        },
    },
    {
        "name": CONFIGURE_VAULT_TOOL,
        "description": "Deterministically write Schema Version 2 user/repo config.json, seed missing "
        "vault formatting templates without overwriting existing customized templates, and record "
        "templates/updates.json baselines after the user explicitly confirms settings. Refused without confirmed=true.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "confirmed": {
                    "type": "boolean",
                    "description": (
                        "Must be true after the user explicitly confirms identity, timezone, roots, and connectors"
                    ),
                },
                "scope": {
                    "type": "string",
                    "enum": ["vault", "personal"],
                    "description": "Target setup scope: 'vault' (default) or 'personal' (user profile only)",
                },
                "vault_root": _VAULT_ROOT,
                "user_name": {"type": "string", "description": "User's display name"},
                "user_email": {"type": "string", "description": "User's email address"},
                "timezone": {
                    "type": "string",
                    "description": "Explicit IANA timezone (e.g. 'America/Chicago', never 'system')",
                },
                "priorities": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of personal priorities stated by the user",
                },
                "projects_root": {
                    "type": "string",
                    "description": "Vault-relative (default: '1-projects') or explicit absolute path",
                },
                "daily_plans_relative": {
                    "type": "string",
                    "description": "Vault-relative daily plans folder (default: '2-areas/daily-plans')",
                },
                "templates_dir": {
                    "type": "string",
                    "description": "Vault-relative templates folder (default: './3-resources/templates')",
                },
                "harness_connections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "source": {"type": "string"},
                            "via": {"type": "string"},
                        },
                        "required": ["source", "via"],
                        "additionalProperties": False,
                    },
                    "description": "Read-only host integrations confirmed by the user (source + via)",
                },
                "standalone_sources": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Standalone read-only connectors enabled by the user",
                },
                "disabled_sources": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Communication sources explicitly disabled by the user",
                },
                "initial_lookback_days": {
                    "type": "integer",
                    "description": "Positive integer lookback window in days on first pull (default: 7)",
                },
                "set_default_vault": {
                    "type": "boolean",
                    "description": "Bind vault_root as defaultVaultRoot in user config.json (default: true)",
                },
            },
            "required": ["confirmed"],
            "additionalProperties": False,
        },
    },
)
