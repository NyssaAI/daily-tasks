---
name: daily-tasks-plan
description: Create or edit the user's local-day Markdown plan across personal and delegated work; review available work and carry unfinished selected work forward without ranking, scheduling or fitting durations.
---

# Plan the day

Bind this session to one resolved vault, its assigned projects root and daily-plan
root. Shared user preferences do not combine vaults. Carry the context binding with
inventory, numbered screens and recovery state; reject another vault's binding.

Apply [response conventions](../daily-tasks/references/response-conventions.md)
when rendering review screens and interpreting numbered replies.
Use the [inventory and planning flow](../daily-tasks/references/planning-flow.md)
for context, cache, maintenance, selection screens and future-day writes. Load the
configured `templates.planDayReview` or the bundled
[review screen](../daily-tasks/assets/plan-day-select-tasks-screen.md) when displaying
the ownership-focused review or recap. The saved daily plan uses its own template.
In task-addition screens sort projects by their directory dates, oldest first,
breaking ties alphabetically by name; undated directories follow alphabetically
by name. Preserve each project's task order from its index.
Offer only the first incomplete milestone per project unless the user asks
for all milestones; skip terminal milestones and preserve existing selections.
Resolve an unknown milestone/task sequence rather than inventing priority or UUID ordering.
Paginate available additions at 15 rows maximum, with stable response handles and
Show more. Exclude explicit future-day selections from today's addition options;
a future target_date alone is not future selection. Keep counts for the full scoped
inventory. Canonical task-state replies do not implicitly add work to today.
Apply status replies via records: canonical tasks/required parent changes and
project views first, then daily-plan projection. Clarify ambiguous commands before
affected writes and preserve pending recovery when any required effect fails.

## Keep routine planning scoped

Resolve and read the existing profile first; do not restart setup for a configured
user. Reuse guidance already loaded in this session. Read today's plan and its
dated rollover state. If rollover is not verified complete, list the daily-plan
directory to find the most recent earlier plan even when today's file exists.
Read the selected rows' referenced records and the baselines needed to reconcile
them. Inspect parent records, blockers and dependencies only when needed to verify
a change or explain a suggestion. Use `project-index` to obtain available project
work as well as selected work; reuse its verified cache instead of repeating agent
file exploration. A cold/stale cache scans deterministically. Do not run a full
decision-history query merely to open/carry a daily plan. Preserve unresolved
references rather than guessing their identity.
Recover applicable pending operations before applying affected changes. Unchanged
reads need no checkpoint, log event or rewritten baseline. Batch independent reads
and checks when supported; keep dependent writes and log appends ordered. This
scope rule preserves validation and reconciliation for every affected change.

Read configured profile and [records](../daily-tasks/references/records.md),
[operation protocol](../daily-tasks/references/operations.md). Reconcile edits before
refreshing any existing plan. Use `local-day` for today's date and `format-time` for
display; ALWAYS identify local timezone in the heading and all rendered times.
When the profile uses `"system"`, resolve the host's actual timezone via
`validate-profile`'s `resolvedTimezone` and use that zone consistently for this
planning run. Render the actual zone name, never the word "system".

Use `<vaultRoot>/<dailyPlansRelative>/YYYY.MM.DD-daily-plan.md` (default
`2-areas/daily-plans`). This is user output. Load the path settings from
`<configRoot>/profile.json`; the profile's directory is not the daily-plan directory.
Never save a daily plan in configRoot or `.nyssaai/daily-tasks/`. Resolve missing output
settings using [setup](../daily-tasks-setup/SKILL.md), including its known-vault default.
Ask only if output scope remains unknown or points into configuration/state storage;
do not fall back to configRoot or cwd.
Open today's plan if present; create it only if missing, with
UUIDv7 identity and created/updated GMT timestamps. Do not backfill skipped days.
Explicit future selections create that date's missing plan through planning-flow.
Use the once-per-day rollover protocol in planning-flow regardless of plan-file
existence. Reconcile the most recent prior plan, then merge its unfinished selections
by UUID into today's existing selections, preserving both. Completed/cancelled items
remain historical. Honor explicit removals and other future allocations; never
repopulate from all open tasks. Missing records remain visible unresolved references.
Only verified rollover completion skips this merge on later same-day requests;
recover an interrupted checkpoint before reconsidering its effects.

Separate **My work** (effective assignee current user's email) and **Delegated work**
(owner current user, effective assignee another human/agent). Optional assignee falls
back to owner; no unassigned category. Include work assigned to user even if owned by
another person. Delegated completion belongs to its doer; suggested follow-up is a new
candidate, not a silently created obligation. Ownership alone doesn't authorize external
messages or taking over delegated execution.

Use the profile's `templates.dailyPlan` when supplied, following
[custom templates](../daily-tasks/references/templates.md); otherwise use the
[daily-plan template](../daily-tasks/assets/daily-plan.md). Each row references one
task ID and relative wiki link. Preserve stable display order and existing edits;
list position does not prescribe execution order. Present available work for user
selection without ranking it or asking for an ordering decision. Execution order
belongs to the person. Never calculate time budgets, schedule slots, change targets, or try to
fit work into a timeframe. Carry-forward is already authorized and requires no new
acceptance; adding previously unselected work requires a supplied planning decision.

Keep the saved plan readable: one checkbox per task, a descriptive link label and
hidden ref comment. When a title needs context, add one indented plain-text line
with the project, assignee for delegated work, or concrete blocker. Do not expose
IDs or repeat full task metadata. Do not silently reorder selections. Under an empty
section write a short sentence such as "No delegated work selected." rather than
leaving an unexplained blank heading. Omit blank placeholder rows. In chat, link
the saved plan first, then summarize changes and outstanding decisions without
reprinting the whole plan unless the user asks to see it.

Removing row = deselect, task remains open and stops future carry-forward until selected.
Log deselection and selection once when changed. Manual checkbox edits
update the canonical task on reconciliation; a new text-only checkbox becomes candidate.
Do not record unchanged check-ins/reads. On repeated same-day calls preserve valid edits,
completed/cancelled visibility and plan identity; don't rebuild a second plan.
