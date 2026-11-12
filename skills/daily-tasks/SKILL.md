---
name: daily-tasks
description: Use this skill when the user asks to "set up Daily Tasks", "capture possible tasks from notes", "create or update a project, milestone, or task", "fix malformed record files", "plan my day", or "check in and reconcile edits". Manages personal projects, milestones, accepted tasks, external blockers, daily plans, and anytime check-ins using editable Markdown records and the daily-tasks MCP server. Do NOT use this skill for calendar time-blocking or scheduling work into available time slots.
---

# Daily Tasks

Supply capabilities to the calling agent; do not assume its persona or autonomously run a personal operating system. Maintain one authoritative Markdown record per item and route each request to the matching workflow:

| Request | Load |
| --- | --- |
| First use, setup incomplete on any gate, identity, timezone, paths, priorities, MCP registration, connectors, formatting templates | [Setup](workflows/setup.md) |
| Extract possible work or accept a batch | [Capture](workflows/capture.md) |
| Create/update/move/assign work, DoD, dependencies, blockers, or fix malformed files | [Records](workflows/records.md) |
| Select daily work or change today's list | [Daily plan](workflows/plan.md) |
| Report progress, reconcile edits, resume or check in | [Check-in](workflows/checkin.md) |

## Mandatory full-setup gate

Daily Tasks **must not run** downstream workflows ([Capture](workflows/capture.md), [Records](workflows/records.md), [Daily plan](workflows/plan.md), or [Check-in](workflows/checkin.md)) unless setup is completely finished. Always verify setup deterministically through the bundled MCP server (`daily_tasks_setup_status(vault_root="<vaultPath>")`) rather than guessing file layouts or hand-editing JSON:
- **Configuration (`user_home` -> `repo_root`)**: `~/.nyssa-ai/daily-tasks/profile.json` (and optional `<repo_root>/.nyssa-ai/daily-tasks/profile.json`) with `schema_version: 2`, `user.name`, `user.email`, `timezone`, `priorities`, optional `defaultVaultRoot`, and per-vault overrides under `vaults`.
- **Vault (`vault_root`)**: Contains Markdown projects (`1-projects` by default), daily plans (`2-areas/daily-plans` by default), and visible templates (`./3-resources/templates` by default), with **zero** `.nyssa-ai/` directories inside `vault_root`. Never bind an agent runtime root (`SOUL.md` + `IDENTITY.md`) as `vault_root`.
- **Runtime state (`runtime_root`)**: Mutable operational state (`fetch-cursors.json`, `suggestions.json`, `decision-log.json`, `sessions/`) lives in `runtime_root` (`--runtime-root` -> `NYSSA_RUNTIME_ROOT` -> agent persona `cwd` with `SOUL.md`+`IDENTITY.md` -> `~/.nyssa-ai/daily-tasks/runtime/`).

Before executing any non-setup workflow, verify **all four** setup gates (reported by `daily_tasks_setup_status`):
1. **Live MCP tools in current harness**: `daily_tasks_*` MCP tools (`daily_tasks_setup_status`, `daily_tasks_configure_vault`, `daily_tasks_start_session`, `daily_tasks_get_fetch_window`, `daily_tasks_execute_operations`, `daily_tasks_advance_screen`, `daily_tasks_confirm_plan`, `daily_tasks_get_session_state`, `daily_tasks_cancel_session`) are registered and callable in the active harness (use `tool_search` / `catalog.search("daily_tasks")` first when tool search is active).
2. **Schema Version 2 profiles and roots**: `~/.nyssa-ai/daily-tasks/profile.json` exists with `"schema_version": 2`, resolving `user.email`, an explicit IANA `timezone` (never `"system"`), `projectsRoot` (default `"1-projects"`), and `dailyPlansRelative` (default `"2-areas/daily-plans"`).
3. **Vault templates baseline**: Active formatting templates in `<vault_root>` and `~/.nyssa-ai/daily-tasks/templates/updates.json` are present.
4. **Communication sources configured**: Connector selections and `initialLookbackDays` are recorded under `sources` in `profile.json`.

If **any** gate above fails:
- **Immediately halt** the downstream workflow and load [Setup](workflows/setup.md) (with [harness-aware setup](references/harness-setup.md)) to inspect via `daily_tasks_setup_status`, confirm choices with the user, and persist via `daily_tasks_configure_vault(confirmed=true, ...)`.
- **Never** hand-author `profile.json` or vault templates when `daily_tasks_configure_vault` is available, **never** create `.nyssa-ai/` inside `vault_root`, **never** manually scan vault Markdown files to synthesize a read-only plan summary, and **never** write or execute ad-hoc Python scripts importing `daily_tasks` internals.
- If a harness requires a session reload or user action before newly registered `daily_tasks_*` MCP tools become callable, stop after completing the harness registration step and ask the user to continue once the MCP tools are active.
- Do not re-run Setup when all four gates are already satisfied unless the user explicitly asks to change settings. Isolate mutable operating state under `runtime_root`, and never enable background monitoring or time-slot scheduling.

## MCP server boundary

- Invoke the `daily-tasks` planning server exclusively via host MCP tool calls (`daily_tasks_*`) as detailed in [Daily plan](workflows/plan.md) and [MCP / CLI interface](references/cli.md).
- **Never** execute `daily-tasks-mcp`, `python -m daily_tasks`, or custom Python scripts calling `PlanningTools` as a CLI command or shell subprocess.
- Mutate disk records through the MCP server only when the user explicitly confirms the plan (`daily_tasks_confirm_plan(confirmed=true)`).
- Consult [harness setup](references/harness-setup.md), [records and views](references/records.md), [operation protocol](references/operations.md), [templates](references/templates.md), and [template updates](references/template-updates.md) when needed by the active workflow.

## Presentation directives

- Lead with the requested result and a clickable Markdown link (`file:///...`) whenever an artifact is created or updated.
- Keep chat replies concise using human-readable titles, compact bullets, and standard Markdown.
- Omit internal implementation details (raw UUIDs, JSON payloads, checkpoints, CLI transcripts, internal state paths) from ordinary user replies.
- Require explicit user acceptance before creating projects, milestones, or tasks (a direct user command to create named work supplies acceptance; notes, quotes, or bare checkboxes do not).
- Render validated `payload.screen` planning screens unchanged per [Daily plan](workflows/plan.md) and [response conventions](references/response-conventions.md); never substitute freeform prose or widgets.

## Verification

Before reporting completion of any Daily Tasks request:
- [ ] Confirm the selected workflow in `workflows/*.md` was loaded and its `## Verification` checklist was satisfied.
- [ ] Confirm all four full-setup gates were verified before any non-setup workflow ran (or that [Setup](workflows/setup.md) was triggered and completed first).
- [ ] Confirm no unaccepted candidate tasks were written to canonical Markdown records, no `.nyssa-ai/` directory was created inside `vault_root`, and no time-fitting or duration scheduling was introduced.
- [ ] Confirm `daily-tasks-mcp` was invoked strictly via host `daily_tasks_*` MCP tools (never via shell subprocesses or ad-hoc Python scripts) and all persisted changes were verified on disk.
