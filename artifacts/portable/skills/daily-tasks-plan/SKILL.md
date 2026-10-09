---
name: daily-tasks-plan
description: Create or edit the user's local-day Markdown plan across personal and delegated work; review available work and carry unfinished selected work forward without ranking, scheduling or fitting durations. Use for "plan my day," selecting accepted tasks for today or a future day, or adding or removing daily selections; selection does not change task status.
---

# Plan the day

Follow these checkpoints in order. A directly activated Plan uses the same contracts
as router-led planning; no earlier router load is required.

## 1. Resolve and prepare

Load [context and planning flow](../daily-tasks/references/planning-flow.md#resolve-once)
when binding the request and preparing inventory. Reuse the configured profile and
already-loaded guidance. Use [Setup](../daily-tasks-setup/SKILL.md) only for unresolved
settings or an explicit configuration change; do not restart setup for a configured user.
Bind one vault, its assigned projectsRoot and dailyPlansRoot throughout this session,
numbered replies and recovery. Shared preferences never combine vaults.

Start with `planning-prepare`, passing the captured absolute vault binding and known
explicit profilePath. It resolves actual dated plan identities/hashes, full-graph
inventory, rollover/review proposals, pending operations, maintenance and enrollment
issues. Use this packet instead of temporary orchestration or hand-assembled parse
results. Selected records alone are not the validation universe. Preparation does
not reconcile edits, complete rollover or finish check-in.

Use the packet's localDate and actual resolved timezone. Load the [CLI](../daily-tasks/references/cli.md)
when invoking operations, `local-day` or `format-time`; identify the actual local zone
in the heading and rendered times, never the profile value `"system"`.
Daily output is `<vaultRoot>/<dailyPlansRelative>/YYYY.MM.DD-daily-plan.md`, normally
`2-areas/daily-plans`, resolved from the profile. Never use configRoot, operating
state or a later cwd as output. Setup resolves its known-vault default; ask only if
scope remains unknown or points into configuration/state storage.

## 2. Recover and reconcile

Load [operations](../daily-tasks/references/operations.md) before recovery,
reconciliation or consequential writes, and [record conventions](../daily-tasks/references/records.md)
when validating affected records/links. Inspect current-plan edits and per-view
baselines; recover applicable pending operations before applying affected changes.
Read selected canonical records and needed parents, blockers/dependencies without
repeating a full history query merely to open/carry a plan. Preserve unresolved
references instead of guessing identity. A fresh cache never skips these checks.

Apply the [requested-use maintenance gate](../daily-tasks/references/planning-flow.md#load-and-maintain).
Compare edits before regenerating any view; suspend only conflicting items and
continue independent changes. Manual status edits update canonical records through
[Records](../daily-tasks-records/SKILL.md); unidentified new checkboxes go to
[Capture](../daily-tasks-capture/SKILL.md) as candidates. Unchanged reads need no
checkpoint, event or rewritten baseline. Batch independent reads/checks; keep
writes and log appends ordered.

After reconciled writes, invalidate/refresh affected inventory and run
`planning-prepare` again. Any write changing the packet's source or state hashes
requires a fresh packet before a dependent state action or review is saved.

## 3. Verify rollover

Load [once-per-day rollover](../daily-tasks/references/planning-flow.md#once-per-day-rollover)
before opening/creating or merging today's plan. Preserve an existing plan's UUID,
selections, prose and valid edits; create only a missing plan with UUIDv7 and GMT
creation/update timestamps. Never backfill skipped days. A pre-created future plan
still needs verified rollover for today. Find and reconcile the most recent earlier
plan when dated rollover is incomplete, even if today's file already exists.

Merge only unfinished prior selections by UUID into existing selections. Honor
explicit removals/future allocations; never populate from all open tasks. Terminal
rows remain historical and missing records remain unresolved. Carry-forward is
already authorized; it needs no new acceptance. Recover interrupted checkpoints
before reconsidering effects, and carry only once after verified dated completion.

Changed rollover uses the Markdown checkpoint, optimistic checks, script-only log,
view/baseline and completion protocol in planning-flow. Retain its checkpoint until
all required effects are verified. An eligible no-change rollover instead uses
`planning-state` action `complete-rollover` with fresh packet hashes and context.now; it
creates a receipt, no log event. Outstanding effects/unresolved carry are not eligible.
Reprepare after changed Markdown or state writes before preparing the review.

## 4. Render and save the review mapping

Load [review scope](../daily-tasks/references/planning-flow.md#review-scope),
[durable mapping](../daily-tasks/references/planning-flow.md#build-and-review)
and [response conventions](../daily-tasks/references/response-conventions.md) before
rendering or waiting for numbered replies. Use the prepared owner-focused review,
its full scoped counts, stable ordering, first incomplete milestones, future
exclusions and pages of at most 15 additions. Existing out-of-view selections survive.
Persist the displayed UUID/number mapping, binding and local date with `planning-state`
action `save-review` before waiting. Load the [CLI inputs](../daily-tasks/references/cli.md)
for the packet's complete hashes and matching page/allMilestones options. A changed
inventory/mapping requires a fresh screen; never reinterpret old numbers. Reprepare
using saved mappings, preserving unchanged identities' numbers across writes, pages
and follow-ups.

When authoring either document, load [custom templates](../daily-tasks/references/templates.md)
if configured/supplied. `templates.planDayReview` controls chat; `templates.dailyPlan`
controls saved output independently. Otherwise load the bundled [review screen](../daily-tasks/assets/plan-day-select-tasks-screen.md)
or [daily-plan template](../daily-tasks/assets/daily-plan.md) for that document's visible
layout. Use the [saved-plan contract](../daily-tasks/references/planning-flow.md#saved-daily-plan)
for personal/delegated responsibility and retaining only selected work. Existing
layout/prose survives ordinary updates. Template registration does not authorize
rewriting records or accepting sample work.

## 5. Apply explicit decisions

Resolve replies against the saved screen using response conventions. A bare number
needs an action; clarify only affected items, retain clear batch decisions and save
progress before waiting. Silence and omitted rows never supply acceptance.
Adding previously unselected work requires a supplied planning decision. Removing
a row deselects it, leaves its task open and stops future carry until selected.
Log changed selection/deselection once; never log unchanged reads/check-ins.

Status/ownership/closure changes go through [Records](../daily-tasks-records/SKILL.md):
canonical tasks, required parents and project views first, daily projection second.
Status reports do not select work. Preserve owner authority and explicit acceptance;
a user's explicit request to create named work can be acceptance, while quoted
requests, inferred promises and new text-only checkboxes remain Capture candidates.
A failure retains the pending checkpoint and the exact incomplete effects.
For explicit future dates use the [future-selection transaction](../daily-tasks/references/planning-flow.md#future-selection-transaction),
creating only that missing date's plan and preserving one active date per task.
Reprepare after writes invalidate packet hashes before another review/state action.

Never rank selections, request an execution-order decision, calculate time budgets,
schedule slots, change targets or fit work into a timeframe. Execution order belongs
to the person; planning never authorizes external messages or delegated execution.

## 6. Verify and report

Verify affected records, parent/closure effects, project/daily views, script-only log
results and baselines under operations before completing checkpoints. Preserve
completed/cancelled visibility, explicit removals and today's plan identity on repeated
calls. Failed receipts, unfinished operations or conflicts remain pending and resumable.
Verify rollover completion separately from first review and successful check-in.

Link the saved plan first; summarize applied changes, outstanding decisions and exact
failed effects without reprinting the entire plan unless requested. Use the review's
same layout/numbers for today's recap. Future tables require an explicit week-view
request. A preview or fictional example cannot claim saved output.
