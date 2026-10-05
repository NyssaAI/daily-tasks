---
name: daily-tasks-plan
description: Create or edit the user's local-day Markdown plan across personal and delegated work; suggest priorities from explicit preferences and carry unfinished selected work forward without scheduling or fitting durations.
---

# Plan the day

Read configured profile and [records](../daily-tasks/references/records.md),
[operation protocol](../daily-tasks/references/operations.md). Reconcile edits before
refreshing any existing plan. Use `local-day` for today's date and `format-time` for
display; ALWAYS identify local timezone in the heading and all rendered times.

Use `<vaultRoot>/<dailyPlansRelative>/YYYY.MM.DD-daily-plan.md` (default
`2-areas/daily-plans`). This is user output. Load the path settings from
`<configRoot>/profile.json`; the profile's directory is not the daily-plan directory.
Never save a daily plan in configRoot or `.nyssaai/daily-tasks/`. Resolve missing output
settings using [setup](../daily-tasks-setup/SKILL.md), including its known-vault default.
Ask only if output scope remains unknown or points into configuration/state storage;
do not fall back to configRoot or cwd.
Open today's plan if present; create it only if missing, with
UUIDv7 identity and created/updated GMT timestamps. Do not backfill skipped days.
If absent, find most recent prior plan by valid local-date filename, reconcile that plan's
edits, then carry selected unresolved work from it. Completed/cancelled items remain in
the old plan and never carry. Respect explicit removal: never repopulate from all open
tasks. Dedupe by UUID; missing records remain visible unresolved references.

Separate **My work** (effective assignee current user's email) and **Delegated work**
(owner current user, effective assignee another human/agent). Optional assignee falls
back to owner; no unassigned category. Include work assigned to user even if owned by
another person. Delegated completion belongs to its doer; suggested follow-up is a new
candidate, not a silently created obligation. Ownership alone doesn't authorize external
messages or taking over delegated execution.

Use [daily-plan template](../daily-tasks/assets/daily-plan.md). Each row references one
task ID and relative wiki link. Keep order chosen by user/caller, showing explicit
priority-suggestion reasoning from profile and task context. Suggest selection/order;
user decides. Never calculate time budgets, schedule slots, change targets, or try to
fit work into a timeframe. Carry-forward is already authorized and requires no new
acceptance; adding previously unselected work requires a supplied planning decision.

Removing row = deselect, task remains open and stops future carry-forward until selected.
Log deselection and chosen order/selection once when changed. Manual checkbox edits
update the canonical task on reconciliation; a new text-only checkbox becomes candidate.
Do not record unchanged check-ins/reads. On repeated same-day calls preserve valid edits,
completed/cancelled visibility and plan identity; don't rebuild a second plan.
