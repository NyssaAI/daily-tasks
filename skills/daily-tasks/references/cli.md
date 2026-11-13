# Python MCP server and CLI interface

> [!IMPORTANT] Scope Directive
> This reference owns the invocation contracts, runtime flags, stdio stream discipline, and tool/receipt schemas for the `daily-tasks-mcp` stdio server (`src/daily_tasks/cli.py`, `python -m daily_tasks`), interactive Gmail OAuth helper (`python -m daily_tasks.communications.gmail`), out-of-band secret capture helper (`python -m daily_tasks.communications.secret`), and repository packaging scripts (`scripts/assemble.py`, `scripts/validate.py`). It does NOT own step-by-step workflow execution (owned by `workflows/*.md`), Markdown record schemas (owned by [`records.md`](records.md)), or planning domain invariants (owned by [`planning-flow.md`](planning-flow.md)).

## Architectural boundary: MCP vs. terminal helpers

The planning server `daily-tasks-mcp` is an MCP stdio server and must only be invoked via the MCP protocol through host tool calls (`daily_tasks_*`). Self-contained harness-adapter discovery is declared via root `.mcp.json` (`python3 ${CLAUDE_PLUGIN_ROOT}/src/daily_tasks/launch_mcp.py`), generated portable `mcp.json` (`python3 ${PLUGIN_ROOT}/src/daily_tasks/launch_mcp.py`), and Antigravity `mcp_config.json`, while harness-specific discovery and registration details live in [`harness-setup.md`](harness-setup.md). `launch_mcp.py` runs `daily_tasks.cli:cli` directly in-process when Python `>=3.12` dependencies are importable and falls back to `uv run --directory <plugin_root> daily-tasks-mcp` (pointing `UV_PROJECT_ENVIRONMENT` at `<runtime_root>/.venv`) otherwise. When loaded by hosts like OpenClaw, Antigravity, Claude, Codex, Cursor, or Hermes, `daily-tasks-mcp` boots cleanly without startup flags, immediately serving deterministic setup tools (`daily_tasks_setup_status`, `daily_tasks_configure_vault`) while enforcing Schema Version 2 setup on every planning session or fetch-window call (refusing execution whenever setup is incomplete or an agent runtime root containing `SOUL.md` + `IDENTITY.md` is passed as `vault_root`):
1. **Configuration (`user_home` -> `repo_root`)**: `~/.nyssa-ai/daily-tasks/config.json` and optional `<repo_root>/.nyssa-ai/daily-tasks/config.json` (`"schema_version": 2`, resolving `user.email`, `user.name`, explicit IANA `timezone`, optional `defaultVaultRoot`, optional `telemetry.enabled` defaulting to `false`, and `projectsRoot` / `dailyPlansRelative` defaulting to `"1-projects"` and `"2-areas/daily-plans"`, with read-only fallback to legacy `profile.json` when `config.json` is absent). Zero `.nyssa-ai/` directories are ever read from or written inside `vault_root`.
2. **Runtime state (`runtime_root`)**: Resolved deterministically in order: (1) `--runtime-root` -> (2) `NYSSA_RUNTIME_ROOT` (routing `SOUL.md` + `IDENTITY.md` roots to `.nyssa-ai/daily-tasks/runtime`) -> (3) `<cwd>/.nyssa-ai/daily-tasks/runtime` when `cwd` contains `SOUL.md` + `IDENTITY.md` (`is_agent_runtime_root`) -> (4) configured `runtimeRoot` in `config.json`, `<repo_root>/.nyssa-ai/daily-tasks/runtime/` when `<repo_root>/.nyssa-ai/daily-tasks` exists, or default `~/.nyssa-ai/daily-tasks/runtime/`. Opt-in usage telemetry (`"telemetry": {"enabled": true}`) appends JSONL events to `<runtime_root>/usage/events.jsonl` and creates zero `usage/` directories when disabled (`false` by default).

The active vault can be supplied per call via `vault_root`, bound as `defaultVaultRoot` in `~/.nyssa-ai/daily-tasks/config.json` via `daily_tasks_configure_vault`, or passed at startup via `--vault-root`.

Agents must never execute `daily-tasks-mcp` or `python -m daily_tasks` as a one-shot CLI command or shell subprocess. Direct terminal execution is reserved exclusively for interactive user-driven Gmail authorization (`python -m daily_tasks.communications.gmail`), user-run out-of-band secret capture (`python -m daily_tasks.communications.secret`), or repository packaging and validation scripts (`scripts/assemble.py`, `scripts/validate.py`).

```text
uv run daily-tasks-mcp [--vault-root ABSOLUTE_VAULT] [--runtime-root ABSOLUTE_RUNTIME] [--repo-root ABSOLUTE_REPO] [--user-email EMAIL] [--user-name NAME] [--timezone TZ] [--projects-root PATH] [--daily-plans-root PATH] [--initial-lookback-days DAYS] [--log-file PATH] [--config-dir ABSOLUTE_CONFIG_DIR]
uv run python -m daily_tasks [--vault-root ABSOLUTE_VAULT]
uv run python -m daily_tasks.communications.gmail --config-dir ABSOLUTE_CONFIG_DIR [--redirect-port PORT]
uv run python -m daily_tasks.communications.secret [--config-dir ABSOLUTE_CONFIG_DIR] capture NAMESPACE KEY [--prompt TEXT] [--provider NAME] [--forced-provider NAME] [--mode auto|cli|web]
uv run python -m daily_tasks.communications.secret gmail [--no-client-secret] | slack
uv run python -m daily_tasks.communications.secret vault --name NAME --kind bitwarden-secrets|bws|bitwarden [--endpoint URL] [--project-id ID] [--organization-id ID]
python3 scripts/assemble.py [write|check] [--output-dir DIR]
python3 scripts/validate.py
```

The `--initial-lookback-days` flag (a positive integer) bounds a communication source's first pull when no saved cursor exists. When unset on the command line, the server reads `sources.initialLookbackDays` and then top-level `initialLookbackDays` from `config.json`, defaulting to `7`. Supplying a non-positive value causes the process to exit with code `2` and emit a diagnostic message on `stderr`. Fetch cursors are read from and persisted to `<runtime_root>/fetch-cursors.json`.

Stdout is reserved strictly for MCP JSON-RPC 2.0 frames so host transports never encounter corrupted protocol payloads. All structured diagnostic logs are emitted to `sys.stderr` and controlled via `DAILY_TASKS_LOG_LEVEL` and optional `--log-file`.

## Runtime invariants and platform rules

### Host clock and timestamp rationale

When starting a planning session for the current day, callers omit the explicit `date` parameter from `daily_tasks_start_session` so the server resolves the current local day in the configured IANA timezone. All persisted and logged event timestamps use UTC ISO-8601 format ending in `Z`. The server never fabricates timestamp precision or mutates unrelated Markdown lines; all record updates flow through `FileStoreLocal` Concrete Syntax Tree (CST) updates.

### Windows and PowerShell encoding safety

On Windows, PowerShell redirection operators (`>` and `Out-File`) default to UTF-16LE with BOM, which corrupts UTF-8 Markdown records and JSON state files. File modifications must use UTF-8 without BOM, and JSON payloads must preserve exact ISO-8601 timestamp strings without reparsing them into locale-dependent `.NET` `DateTime` objects.

## MCP tools matrix

| Tool | Arguments | Result / Effect |
| --- | --- | --- |
| `daily_tasks_setup_status` | `vault_root?` (`string`) | Read-only inspection of `user_home` / `repo_root` Schema Version 2 `config.json`, vault layout, existing formatting templates, `templates/updates.json`, and all four setup gates (`setup_complete`, `missing_gates`, `proposed_settings`). Writes nothing. |
| `daily_tasks_configure_vault` | `confirmed` (`true`), `scope?` (`vault` \| `personal`), `vault_root?`, `user_name?`, `user_email?`, `timezone?`, `priorities?`, `projects_root?`, `daily_plans_relative?`, `templates_dir?`, `harness_connections?`, `standalone_sources?`, `disabled_sources?`, `initial_lookback_days?`, `set_default_vault?` | Validates explicit IANA timezone, containment rules, and non-agent-runtime `vault_root`; writes Schema Version 2 `config.json` in `user_home` (binding `defaultVaultRoot` when `set_default_vault=true`), seeds missing formatting templates without overwriting customized templates, and records `templates/updates.json` in `user_home`. Refused without `confirmed=true`. |
| `daily_tasks_start_session` | `date?` (`YYYY-MM-DD`), `focus?` (`string`), `messages?` (`[CommunicationMessage]`, `docs/specs/message.json`), `checked_sources?` (`[string]`), `vault_root?` (`string`) | Parses Markdown vault records via `ProjectPlanRepositoryMarkdown` and `DailyPlanRepositoryMarkdown`, builds in-memory `StateGraph`, fetches unread messages via configured `CommunicationClient` implementations, filters host-supplied `messages` against each source's fetch window, runs deterministic pre-matching, generates `Suggestions`, and returns `session_id` + Screen 1 (`payload.screen`). Performs no disk writes. |
| `daily_tasks_get_fetch_window` | `sources?` (`[string]`, default `gmail`, `slack`), `vault_root?` (`string`) | Returns `payload.fetch_windows[]` (`source`, `has_cursor`, `since`, `after_epoch`, `last_external_id`, `initial_lookback_days`) and `payload.initial_lookback_days`: the saved cursor from `<runtime_root>/fetch-cursors.json`, or `now - initial_lookback_days` (7 by default) on a first pull. Sessionless; writes nothing. |
| `daily_tasks_execute_operations` | `session_id`, `original_words`, `verdicts?` (`[{row, verdict, edits?}]`), `operations?` (`[Operation]`) | Validates and stages user verdicts (`accept`, `edit`, `reject`) and planning operations (`assign-to-day`, `unplan`, `set-status`, `reassign`) all-or-nothing in memory; returns updated `payload.screen`. |
| `daily_tasks_advance_screen` | `session_id`, `target_screen` (`2` or `3`) | Advances to Screen 2 (per-project task day assignment) or Screen 3 (confirmation recap) and returns `payload.screen`. |
| `daily_tasks_confirm_plan` | `session_id`, `confirmed` (`true`) | Applies staged `RecordChange` updates via `FileStoreLocal`, renders and writes `YYYY.MM.DD-daily-plan.md`, appends entries to `<runtime_root>/decision-log.json`, and saves `<runtime_root>/suggestions.json`, `<runtime_root>/sessions/YYYY.MM.DD.json`, and `<runtime_root>/fetch-cursors.json`. |
| `daily_tasks_get_session_state` | `session_id` | Re-renders and returns the current session screen and staged state without side effects. |
| `daily_tasks_cancel_session` | `session_id` | Discards the active in-memory session without modifying any disk records. |
| `daily_tasks_capture_secret` | `namespace`, `key`, `prompt_message?`, `provider?` | Opens a one-time `127.0.0.1` loopback page where the user types the secret, stores it in `aesLocal` (default), `literal`, or a configured cloud key vault, and returns `payload` (`namespace`, `key`, `provider`, `stored_at`). The secret never appears in arguments, replies, or logs. |

## Out-of-band secrets architecture

Secrets live in the keyring-protected `NyssaAI.Configuration` store under `--config-dir` (defaulting to `~/.nyssa-ai/daily-tasks`). Well-known secret addresses include `communication/gmail-client-id`, `communication/gmail-client-secret`, `communication/slack`, and `vault/<name>-access-token`.

The `secret` helper (`python -m daily_tasks.communications.secret`) prints only the structured receipt to `stdout` while routing user prompts and the loopback URL to `stderr`. Running with `--mode auto` uses masked terminal input when `stdin` is a TTY and falls back to the local loopback browser page otherwise. The `vault` subcommand seals the cloud vault's access token locally and registers the vault in the configuration manifest (`bitwarden-secrets`, `bws`, and `bitwarden` by default).

## Decision log entry schema

Decision log entries appended to `<runtime_root>/decision-log.json` conform to `docs/specs/decision-log-entry.json`:

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
