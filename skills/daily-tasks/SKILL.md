---
name: daily-tasks
description: Use this skill when the user asks to "set up Daily Tasks", "capture possible tasks from notes", "create or update a project, milestone, or task", "fix malformed record files", "plan my day", or "check in and reconcile edits". Manages personal projects, milestones, accepted tasks, external blockers, daily plans, and anytime check-ins using editable Markdown records and the daily-tasks MCP server. Do NOT use this skill for calendar time-blocking or scheduling work into available time slots.
---

# Daily Tasks

Supply capabilities to the calling agent; do not assume its persona or autonomously run a personal operating system. Maintain one authoritative Markdown record per item and route each request to the matching workflow:

| Request | Load |
| --- | --- |
| First use, project setup not done, identity, timezone, paths, priorities, formatting templates | [Setup](workflows/setup.md) |
| Extract possible work or accept a batch | [Capture](workflows/capture.md) |
| Create/update/move/assign work, DoD, dependencies, blockers, or fix malformed files | [Records](workflows/records.md) |
| Select daily work or change today's list | [Daily plan](workflows/plan.md) |
| Report progress, reconcile edits, resume or check in | [Check-in](workflows/checkin.md) |

## Configuration and storage gates

Configuration is stored in persistent JSON files under canonical `.nyssa-ai/daily-tasks/profile.json`:
- **User scope**: `~/.nyssa-ai/daily-tasks/profile.json` for personal preferences (`user.name`, `user.email`, `timezone`, `priorities`).
- **Workspace scope**: `<workspaceRoot>/.nyssa-ai/daily-tasks/profile.json` for workspace bindings (`projectsRoot`, `dailyPlansRelative`, `sources`).

Before executing any routed workflow, enforce these resolution gates:
1. Load persistent preferences from canonical profile layers (`~/.nyssa-ai/daily-tasks/profile.json` and `<workspaceRoot>/.nyssa-ai/daily-tasks/profile.json`) or accepted custom pointers without recursively scanning home directories.
2. Resolve `workspaceRoot`, `projectsRoot`, and `dailyPlansRoot` from the bound profile; never infer workspace scope from a later process `cwd` or plugin installation path.
3. Isolate workspace operating state under `<workspaceRoot>/.nyssa-ai/daily-tasks/`.
4. If project setup is not already done (missing `profile.json` or unresolved workspace bindings), immediately trigger and complete [Setup](workflows/setup.md) before attempting [Records](workflows/records.md), [Daily plan](workflows/plan.md), or [Check-in](workflows/checkin.md). Do not re-run Setup when configuration is already complete unless the user explicitly asks to change settings.
5. Preserve `configurationSources` across turns. If the user supplies an invalid path or command, report the exact validation error and ask for clarification.
6. Never enable background monitoring, startup foundation hooks, or autonomous time-slot scheduling.

## MCP server boundary

- Use the `daily-tasks` MCP server exclusively via host MCP tool calls (`daily_tasks_start_session`, `daily_tasks_get_fetch_window`, `daily_tasks_execute_operations`, `daily_tasks_advance_screen`, `daily_tasks_confirm_plan`, `daily_tasks_get_session_state`, `daily_tasks_cancel_session`, `daily_tasks_capture_secret`) as detailed in [Daily plan](workflows/plan.md) and [MCP / CLI interface](references/cli.md).
- **Never** execute `daily-tasks-mcp` or `python -m daily_tasks.server` as a CLI command or shell subprocess.
- Mutate disk records through the MCP server only when the user explicitly confirms the plan (`daily_tasks_confirm_plan(confirmed=true)`).
- Consult [records and views](references/records.md), [operation protocol](references/operations.md), [templates](references/templates.md), and [template updates](references/template-updates.md) when needed by the active workflow.
- If the MCP server or filesystem access is unavailable, report the exact capability gap and provide a read-only proposal; never claim persistence or bypass the decision log.

## Presentation directives

- Lead with the requested result and a clickable Markdown link (`file:///...`) whenever an artifact is created or updated.
- Keep chat replies concise using human-readable titles, compact bullets, and standard Markdown.
- Omit internal implementation details (raw UUIDs, JSON payloads, checkpoints, CLI transcripts, internal state paths) from ordinary user replies.
- Require explicit user acceptance before creating projects, milestones, or tasks (a direct user command to create named work supplies acceptance; notes, quotes, or bare checkboxes do not).
- Render validated `payload.screen` planning screens unchanged per [Daily plan](workflows/plan.md) and [response conventions](references/response-conventions.md); never substitute freeform prose or widgets.

## Verification

Before reporting completion of any Daily Tasks request:
- [ ] Confirm the selected workflow in `workflows/*.md` was loaded and its `## Verification` checklist was satisfied.
- [ ] Verify that project setup was completed first if `profile.json` or required workspace bindings were missing.
- [ ] Confirm no unaccepted candidate tasks were written to canonical Markdown records and no time-fitting or duration scheduling was introduced.
- [ ] Confirm `daily-tasks-mcp` was invoked strictly via MCP tools (never as a shell command) and all persisted changes were verified on disk.
