---
name: daily-tasks
description: Manage personal projects, milestones, accepted tasks, external blockers, daily priorities and anytime check-ins using editable Markdown records. Use when capturing commitments, updating or delegating work, planning a day, or reconciling progress. Does not schedule work into available time.
---

# Daily Tasks

Supply capabilities to the calling agent; do not assume its persona or autonomously
run a personal operating system. One authoritative record per item. Select one route:

| Request | Load |
| --- | --- |
| First use, identity, timezone, paths, priorities | [Setup](../daily-tasks-setup/SKILL.md) |
| Extract possible work or accept a batch | [Capture](../daily-tasks-capture/SKILL.md) |
| Create/update/move/assign work, DoD, dependencies or blockers | [Records](../daily-tasks-records/SKILL.md) |
| Select/order daily work or change today's list | [Daily plan](../daily-tasks-plan/SKILL.md) |
| Report progress, reconcile edits, resume or check in | [Check-in](../daily-tasks-checkin/SKILL.md) |

Load only that route and references it needs. Resolve configuration using
[setup's ordered discovery rules](../daily-tasks-setup/SKILL.md#resolve-configuration-and-scope):
reuse an existing pointer or established `.nyssaai` common state root, then the known
vault convention. A missing explicit configRoot is not a reason to ask for a path.
Read an existing profile or initialize conventional state within resolved scope and
continue the requested work. Ask only for genuinely missing scope/data or conflicting
settings. Do not scan home directories or infer vault scope from cwd or installed code.
No startup foundation, background monitoring or autonomous scheduling.

Projects, milestones and tasks require explicit user acceptance, including batches.
An explicit instruction to create named work (including a named batch) supplies
acceptance; do not ask the user to accept it again. Research, quoted third-party
requests, inferred promises and manual new checkboxes alone do not supply acceptance.
Human owner defaults to current user; only user direction changes it. Optional
assignee is a person email or agent name; absent means owner does the work. Either
people or agents can assign/reassign. Assignment never means work has started.

Use [records and views](references/records.md), [operation protocol](references/operations.md)
and [CLI](references/cli.md) when their operations are needed. Executables perform
deterministic checks; skills author Markdown. Read/write log only through the CLI.
If Node or filesystem access is unavailable, report the exact capability gap and
offer a proposal only; never claim persistence or bypass the log through direct edits.
