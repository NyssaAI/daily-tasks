# Python MCP server and CLI interface

> [!IMPORTANT]
> **MCP Protocol Directive**: The planning server `daily-tasks-mcp` is an MCP stdio server and MUST ONLY be used via the MCP protocol by host tool invocations (`daily_tasks_*`). Agents must NEVER invoke `daily-tasks-mcp` or `python -m daily_tasks.server` as a CLI command or shell subprocess. Direct command execution is strictly for interactive Gmail authorization (`python -m daily_tasks.auth.gmail`) or repository build scripts (`scripts/assemble.py`, `scripts/validate.py`).
>
> **Scope Directive**: This document is the API, ABI, and invocation specification for the Python `daily-tasks-mcp` server (`src/daily_tasks/cli.py`, `python -m daily_tasks.server`), Gmail OAuth helper (`python -m daily_tasks.auth.gmail`), and repository packaging scripts (`scripts/assemble.py`, `scripts/validate.py`). Domain workflows, markdown styling, planning business rules, and user-facing protocols belong in their respective skill and reference documents.

Requires Python >=3.12 (managed via `uv` and `pyproject.toml`) and permitted filesystem/process access. Resolve `PACKAGE_ROOT` from the installed plugin's actual location; never assume a cache path.

```text
uv run daily-tasks-mcp --workspace-root ABSOLUTE_WORKSPACE [--user-email EMAIL] [--user-name NAME] [--timezone TZ] [--projects-root PATH] [--daily-plans-root PATH] [--state-root PATH] [--log-file PATH]
uv run python -m daily_tasks.server --workspace-root ABSOLUTE_WORKSPACE
uv run python -m daily_tasks.auth.gmail --config-dir ABSOLUTE_CONFIG_DIR
python scripts/assemble.py write|check
python scripts/validate.py
```

Stdout is reserved strictly for MCP JSON-RPC 2.0 frames; all structured diagnostic logs are emitted to `sys.stderr` (configurable via `DAILY_TASKS_LOG_LEVEL` and `--log-file`).

## Runtime invariants and platform rules

### Host clock and timestamp rules
- Omit explicit `date` from `daily_tasks_start_session` unless planning for a specific requested date so the server resolves the current local day in the configured timezone.
- All stored and recorded event timestamps use GMT ISO format ending in `Z`.
- Never fabricate precision or mutate unrelated record lines; all record updates go through the surgical Concrete Syntax Tree (CST) writer.

### Windows and PowerShell JSON safety
- Never use PowerShell `>` or `Out-File` to redirect JSON or Markdown files, as Windows PowerShell defaults to UTF-16LE BOM.
- Keep exact ISO timestamp strings in JSON payloads without reparsing into locale-dependent `.NET` `DateTime` objects.

## MCP tools matrix

| Tool | Arguments | Result / Effect |
| --- | --- | --- |
| `daily_tasks_start_session` | `date?` (`YYYY-MM-DD`), `focus?` (`string`) | Parses Markdown workspace records, builds in-memory `StateGraph`, fetches unread messages via configured `CommunicationPort` connectors, runs deterministic pre-matching, generates suggestions, and returns `session_id` + Screen 1 (`payload.screen`). Performs no disk writes to work records. |
| `daily_tasks_execute_operations` | `session_id`, `original_words`, `verdicts?` (`[{row, verdict, edits?}]`), `operations?` (`[Operation]`) | Validates and stages user verdicts (`accept`, `edit`, `reject`) and planning operations (`assign-to-day`, `unplan`, `set-status`, `reassign`) all-or-nothing in memory; returns updated `payload.screen`. |
| `daily_tasks_advance_screen` | `session_id`, `target_screen` (`2` or `3`) | Advances to Screen 2 (per-project task day assignment) or Screen 3 (confirmation recap) and returns `payload.screen`. |
| `daily_tasks_confirm_plan` | `session_id`, `confirmed` (`true`) | Applies staged record changes surgically via `LocalFileStore`, renders and writes `YYYY.MM.DD-daily-plan.md`, appends entries to `.nyssa-ai/daily-tasks/decision-log.json`, and persists fetch cursors. |
| `daily_tasks_get_session_state` | `session_id` | Re-renders and returns the current session screen and staged state without side effects. |
| `daily_tasks_cancel_session` | `session_id` | Discards the active in-memory session without modifying any disk records. |

## Decision log entry schema

Decision log entries appended to `<stateRoot>/decision-log.json` follow `docs/specs/decision-log-entry.json`:

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
