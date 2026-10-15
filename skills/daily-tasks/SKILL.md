---
name: daily-tasks
description: Manage personal projects, milestones, accepted tasks, external blockers, daily priorities and anytime check-ins using editable Markdown records. Use when capturing commitments, updating or delegating work, planning a day, or reconciling progress. Does not schedule work into available time.
---

# Daily Tasks

Supply capabilities to the calling agent; do not assume its persona or autonomously
run a personal operating system. One authoritative record per item. Select one route:

| Request | Load |
| --- | --- |
| First use, identity, timezone, paths, priorities, formatting templates | [Setup](../daily-tasks-setup/SKILL.md) |
| Extract possible work or accept a batch | [Capture](../daily-tasks-capture/SKILL.md) |
| Create/update/move/assign work, DoD, dependencies or blockers | [Records](../daily-tasks-records/SKILL.md) |
| Select daily work or change today's list | [Daily plan](../daily-tasks-plan/SKILL.md) |
| Report progress, reconcile edits, resume or check in | [Check-in](../daily-tasks-checkin/SKILL.md) |

## Configuration and storage

Configuration is stored in persistent JSON files under canonical `.nyssa-ai/daily-tasks/profile.json`:
- **User scope**: `~/.nyssa-ai/daily-tasks/profile.json` for personal preferences (name, email, timezone, personal priorities).
- **Workspace scope**: `<workspaceRoot>/.nyssa-ai/daily-tasks/profile.json` for workspace bindings (`projectsRoot`, `dailyPlansRelative`).

When loaded, reuse existing accepted pointers or discover persistent `.nyssa-ai` preference layers without re-running setup:
1. Load persistent preferences from canonical profile layers.
2. Resolve `workspaceRoot`, `projectsRoot`, and `dailyPlansRoot` from the profile.
3. Access independent workspace operating state under `<workspaceRoot>/.nyssa-ai/daily-tasks/`.
4. Continue with the requested work. Run [Setup](../daily-tasks-setup/SKILL.md) only on first use when configuration is missing or when the user explicitly requests configuration changes.

Preserve configurationSources through continuation. Do not scan home directories or infer workspace scope from a later process cwd or installed code. If the user provides an invalid path or command, explain the error and request clarification. No startup foundation, background monitoring or autonomous scheduling.

## Present results

- Lead with the requested result and a clickable file link when an artifact exists.
- Keep output concise: use readable titles, compact bullets, and standard Markdown.
- Keep internal details (UUIDs, raw JSON, checkpoints, CLI transcripts, internal state paths) out of ordinary chat replies.
- Projects, milestones, and tasks require explicit user acceptance. A direct instruction to create named work supplies acceptance; notes, quotes, or bare checkboxes do not.
- For interactive planning/review screens, follow [Daily plan](../daily-tasks-plan/SKILL.md) and [response conventions](references/response-conventions.md). Do not substitute freeform prose or widgets for the validated planning screen.
- Route formatting, template choices, and updates to [templates](references/templates.md) and [template updates](references/template-updates.md).

Use [records and views](references/records.md), [operation protocol](references/operations.md)
and [CLI](references/cli.md) when their operations are needed. Executables perform
deterministic checks; skills author Markdown. Read/write log only through the CLI.
If Node or filesystem access is unavailable, report the exact capability gap and
offer a proposal only; never claim persistence or bypass the log through direct edits.
