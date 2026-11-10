# Python MCP server and CLI interface

> [!IMPORTANT] Scope Directive
> This reference owns the invocation contracts, runtime flags, stdio stream discipline, and tool/receipt schemas for the `daily-tasks-mcp` stdio server (`src/daily_tasks/cli.py`, `python -m daily_tasks.server`), interactive Gmail OAuth helper (`python -m daily_tasks.auth.gmail`), out-of-band secret capture helper (`python -m daily_tasks.auth.secret`), and repository packaging scripts (`scripts/assemble.py`, `scripts/validate.py`). It does NOT own step-by-step workflow execution (owned by `workflows/*.md`), Markdown record schemas (owned by [`records.md`](records.md)), or planning domain invariants (owned by [`planning-flow.md`](planning-flow.md)).

## Architectural boundary: MCP vs. terminal helpers

The planning server `daily-tasks-mcp` is an MCP stdio server and must only be invoked via the MCP protocol through host tool calls (`daily_tasks_*`). Self-contained bundle discovery is declared via root `.mcp.json` (`uv run --directory ${CLAUDE_PLUGIN_ROOT} daily-tasks-mcp`), generated portable `mcp.json` (`uv run daily-tasks-mcp`), and Antigravity `mcp_config.json`. When loaded by hosts like Claude, Cursor, Codex, Antigravity, or OpenClaw, `daily-tasks-mcp` boots cleanly from the bundled `pyproject.toml` and `src/` without startup flags. The server dynamically resolves settings across two profile layers:
1. **User profile**: `~/.nyssa-ai/daily-tasks/profile.json` (resolving global `user.email`, `user.name`, and `timezone`).
2. **Workspace profile**: `<workspaceRoot>/.nyssa-ai/daily-tasks/profile.json` (resolving workspace-bound `projectsRoot`, `dailyPlansRelative`, `sources`, and template overrides).

The active workspace can be supplied at startup via `--workspace-root` or dynamically per session via the optional `workspace_root` tool parameter on `daily_tasks_start_session` and `daily_tasks_get_fetch_window`.

Agents must never execute `daily-tasks-mcp` or `python -m daily_tasks.server` as a one-shot CLI command or shell subprocess. Direct terminal execution is reserved exclusively for interactive user-driven Gmail authorization (`python -m daily_tasks.auth.gmail`), user-run out-of-band secret capture (`python -m daily_tasks.auth.secret`), or repository packaging and validation scripts (`scripts/assemble.py`, `scripts/validate.py`).

The runtime requires Python >=3.12 (managed via `uv` and `pyproject.toml`) with permitted filesystem and process access. Callers resolve `PACKAGE_ROOT` from the installed plugin's actual location rather than assuming a host cache path.

```text
uv run daily-tasks-mcp [--workspace-root ABSOLUTE_WORKSPACE] [--user-email EMAIL] [--user-name NAME] [--timezone TZ] [--projects-root PATH] [--daily-plans-root PATH] [--initial-lookback-days DAYS] [--log-file PATH] [--config-dir ABSOLUTE_CONFIG_DIR]
uv run python -m daily_tasks.server [--workspace-root ABSOLUTE_WORKSPACE]
uv run python -m daily_tasks.auth.gmail --config-dir ABSOLUTE_CONFIG_DIR
uv run python -m daily_tasks.auth.secret [--config-dir ABSOLUTE_CONFIG_DIR] capture NAMESPACE KEY [--prompt TEXT] [--provider NAME] [--forced-provider NAME] [--mode auto|cli|web]
uv run python -m daily_tasks.auth.secret gmail [--no-client-secret] | slack
uv run python -m daily_tasks.auth.secret vault --name NAME --kind bitwarden-secrets|bws|bitwarden [--endpoint URL] [--project-id ID] [--organization-id ID]
python scripts/assemble.py write|check
python scripts/validate.py
```

The `--initial-lookback-days` flag (a positive integer) bounds a communication source's first pull when no saved cursor exists. When unset on the command line, the server reads `sources.initialLookbackDays` and then top-level `initialLookbackDays` from the workspace `profile.json`, defaulting to `7`. Supplying a non-positive value causes the process to exit with code `2` and emit a diagnostic message on `stderr`. Fetch cursors are read from and persisted to `<stateRoot>/fetch-cursors.json`.

Stdout is reserved strictly for MCP JSON-RPC 2.0 frames so host transports never encounter corrupted protocol payloads. All structured diagnostic logs are emitted to `sys.stderr` and controlled via `DAILY_TASKS_LOG_LEVEL` and optional `--log-file`.

## Runtime invariants and platform rules

### Host clock and timestamp rationale

When starting a planning session for the current day, callers omit the explicit `date` parameter from `daily_tasks_start_session` so the server resolves the current local day in the configured IANA timezone. All persisted and logged event timestamps use UTC ISO-8601 format ending in `Z`. The server never fabricates timestamp precision or mutates unrelated Markdown lines; all record updates flow through the surgical Concrete Syntax Tree (CST) writer.

### Windows and PowerShell encoding safety

On Windows, PowerShell redirection operators (`>` and `Out-File`) default to UTF-16LE with BOM, which corrupts UTF-8 Markdown records and JSON state files. File modifications must use UTF-8 without BOM, and JSON payloads must preserve exact ISO-8601 timestamp strings without reparsing them into locale-dependent `.NET` `DateTime` objects.

## MCP tools matrix

| Tool | Arguments | Result / Effect |
| --- | --- | --- |
| `daily_tasks_start_session` | `date?` (`YYYY-MM-DD`), `focus?` (`string`), `messages?` (`[Message]`, `docs/specs/message.json`), `checked_sources?` (`[string]`), `workspace_root?` (`string`) | Parses Markdown workspace records, builds in-memory `StateGraph`, fetches unread messages via configured `CommunicationPort` connectors, filters host-supplied `messages` against each source's fetch window, runs deterministic pre-matching, generates suggestions, and returns `session_id` + Screen 1 (`payload.screen`; harness sources appear in `payload.message_sources`). Advanced cursors for connector and `checked_sources` sources are staged until confirmation. A malformed message returns a `Validation` error. Performs no disk writes. |
| `daily_tasks_get_fetch_window` | `sources?` (`[string]`, default `gmail`, `slack`), `workspace_root?` (`string`) | Returns `payload.fetch_windows[]` (`source`, `has_cursor`, `since`, `after_epoch`, `last_external_id`, `initial_lookback_days`) and `payload.initial_lookback_days`: the saved cursor from `<stateRoot>/fetch-cursors.json`, or `now - initial_lookback_days` (7 by default) on a first pull. Sessionless; writes nothing. |
| `daily_tasks_execute_operations` | `session_id`, `original_words`, `verdicts?` (`[{row, verdict, edits?}]`), `operations?` (`[Operation]`) | Validates and stages user verdicts (`accept`, `edit`, `reject`) and planning operations (`assign-to-day`, `unplan`, `set-status`, `reassign`) all-or-nothing in memory; returns updated `payload.screen`. |
| `daily_tasks_advance_screen` | `session_id`, `target_screen` (`2` or `3`) | Advances to Screen 2 (per-project task day assignment) or Screen 3 (confirmation recap) and returns `payload.screen`. |
| `daily_tasks_confirm_plan` | `session_id`, `confirmed` (`true`) | Applies staged record changes surgically via `LocalFileStore`, renders and writes `YYYY.MM.DD-daily-plan.md`, appends entries to `.nyssa-ai/daily-tasks/decision-log.json`, and persists fetch cursors. |
| `daily_tasks_get_session_state` | `session_id` | Re-renders and returns the current session screen and staged state without side effects. |
| `daily_tasks_cancel_session` | `session_id` | Discards the active in-memory session without modifying any disk records. |
| `daily_tasks_capture_secret` | `namespace`, `key`, `prompt_message?`, `provider?` | Opens a one-time `127.0.0.1` loopback page (URL on stderr and in the browser) where the user types the secret, waits for submission (5 minutes), stores it in `aesLocal` (default), `literal` or a configured vault, and returns `payload.receipt` (`namespace`, `key`, `provider`, `stored_at`). The secret never appears in arguments, replies or logs. |

## Out-of-band secrets architecture

Secrets live in the keyring-protected configuration store under `--config-dir` (defaulting to `~/.nyssa-ai/daily-tasks`). Well-known secret addresses include `communication/gmail-client-id`, `communication/gmail-client-secret`, `communication/slack`, and `vault/<name>-access-token`.

The `secret` helper prints only the structured storage receipt to `stdout` while routing user prompts and the loopback URL to `stderr`. Running with `--mode auto` uses masked terminal input when `stdin` is a TTY and falls back to the local loopback browser page otherwise. The `vault` subcommand seals the cloud vault's access token locally—since a vault bootstrap credential cannot reside inside its own vault—and registers the vault in the configuration manifest so subsequent secret captures can target that provider name. Supported vault kinds come from the registered `CloudKeyVaultFactory` set (`bitwarden-secrets`, `bws`, and `bitwarden` by default).

## Decision log entry schema

Decision log entries appended to `<stateRoot>/decision-log.json` conform to `docs/specs/decision-log-entry.json`:

```json
{
  "id": "019a1234-5678-7abc-8def-0123456789ab",
  "session_id": "019a1234-5678-7abc-8def-0123456789ac",
  "decided_at": "2026-11-03T16:30:00Z",
  "origin": "suggestion",
  "verdict": "accepted",
  "original_words": "1 accept",
  "target_ref": {
    "kind": "task",
    "id": "019a1234-5678-7abc-8def-0123456789ad"
  },
  "summary": "Accepted status change to completed"
}
```
