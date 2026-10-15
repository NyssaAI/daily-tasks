---
name: daily-tasks-plan
description: Create or edit the user's local-day Markdown plan across personal and delegated work; review available work and carry unfinished selected work forward without ranking, scheduling or fitting durations. Use for "plan my day," selecting accepted tasks for today or a future day, or adding or removing daily selections; selection does not change task status.
---

# Plan the day

Follow these checkpoints in order. A directly activated Plan uses the same contracts
as router-led planning; no earlier router load is required.

**Screen gate:** Every actual task-selection screen, page, resumed review and planning
recap must use the active review template. Do not replace it with a prose summary,
plain numbered list, question widget or the saved daily-plan layout. Before asking
for choices, draft the screen, pass it as `reviewMarkdown` to `planning-state`
`save-review`, and display the successful result's `value.screen.markdown` unchanged.
A prepared packet or saved number mapping alone is not a validated screen. This gate
does not apply to explanations of how the plugin works or a status-only reply that
presents no planning options. Explicit user formatting changes go through template
selection/overrides; never silently substitute a different layout.

## 1. Resolve and prepare

Load [context and planning flow](../daily-tasks/references/planning-flow.md#resolve-once)
when binding the request and preparing inventory. Reuse the configured profile and
already-loaded guidance. Use [Setup](../daily-tasks-setup/SKILL.md) only for unresolved
settings or an explicit configuration change; do not restart setup for a configured user.
Bind one workspace, its assigned projectsRoot and dailyPlansRoot throughout this session,
numbered replies and recovery. Shared preferences never combine workspaces.

Start with `planning-prepare`, passing the captured absolute workspace binding. On
continuation preserve configurationSources, preferenceOverrides and stateRoot from
the accepted context. Use profilePath only for an explicitly accepted legacy
exclusive profile, never alongside configurationSources. It resolves actual dated plan identities/hashes, full-graph
inventory, rollover/review proposals, pending operations, maintenance and enrollment
issues. Use this packet instead of temporary orchestration or hand-assembled parse
results. Selected records alone are not the validation universe. Preparation does
not reconcile edits, complete rollover or finish check-in.

Use the packet's localDate and actual resolved timezone. Load the [CLI](../daily-tasks/references/cli.md)
when invoking operations, `local-day` or `format-time`; identify the actual local zone
in the heading and rendered times, never the profile value `"system"`.
Daily output is `<workspaceRoot>/<dailyPlansRelative>/YYYY.MM.DD-daily-plan.md`, normally
`daily-plans`, resolved from the profile. Never use configRoot, operating
state or a later cwd as output. Setup resolves its known default; ask only if
scope remains unknown or points into configuration/state storage.

Before authoring the plan or review, follow the packet's `templates` through
[template updates](../daily-tasks/references/template-updates.md). Retain an observed
baseline, offer relevant changes and continue with the active layout while an update
is undecided. Saved-plan and chat-review choices are independent.

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
continue independent changes. When `sources.autoScan` is enabled and no scan receipt
exists in `stateRoot/source-scans/YYYY.MM.DD.json`, run the daily source scan via
[Capture](../daily-tasks-capture/SKILL.md). Manual status edits update canonical records through
[Records](../daily-tasks-records/SKILL.md); unidentified new checkboxes go to
[Capture](../daily-tasks-capture/SKILL.md) as candidates. Unchanged reads need no
checkpoint, event or rewritten baseline. Batch independent reads/checks; keep
writes and log appends ordered.

A blocked maintenance inspection is not a global planning stop. Map diagnostics to
their affected records and paths. Missing navigation targets, baseline enrollment,
invalid legacy projects and unrelated view differences remain maintenance work; they
do not block independent rollover, review mapping or plan saves whose selected and
carried records validate. Suspend only a proposed write that depends on the affected
record or view, and report the remaining maintenance scope separately.

After reconciled writes, invalidate/refresh affected inventory and run
`planning-prepare` again. Any write changing the packet's source or state hashes
requires a fresh packet before a dependent state action or review is saved.

## 3. Verify rollover

Apply [once-per-day rollover](../daily-tasks/references/planning-flow.md#once-per-day-rollover)
before opening/creating or merging today's plan. Preserve an existing plan's UUID,
original `created_at`, selections, prose and valid edits; create only a missing plan
with UUIDv7 and GMT timestamps. Never backfill skipped days. A pre-created future plan
still requires today's verified dated rollover.

Merge unfinished prior selections and all valid in-progress tasks by UUID into
today's selections, honoring carry-forward rules, explicit removals, and future-day exclusions.
In-progress work carries until completed, rescheduled or cancelled. Changed rollover
uses the write-ahead checkpoint and completion protocol; an eligible no-change rollover
finalizes via `planning-state` action `complete-rollover`. Reprepare before the review.

## 4. Render and save the review mapping

Load [review scope](../daily-tasks/references/planning-flow.md#review-scope),
[durable mapping](../daily-tasks/references/planning-flow.md#build-and-review)
and [response conventions](../daily-tasks/references/response-conventions.md) before
rendering or waiting for numbered replies. Scoped review presents all-owner visibility,
stable ordering, lowest incomplete milestones, and one project per page.

Read `packet.templates.templates.planDayReview.active.content` from `planning-prepare`
and author the chat draft matching that exact template. Replace sample rows with
prepared selected/available rows (including hidden `ref` comments, stable numbers, and markers)
and preserve the required legend.
Persist the draft as `reviewMarkdown`, mapping, binding, and local date using `planning-state`
`save-review` before displaying it. If validation fails, correct the draft against the template;
never fall back to an unvalidated layout. Display `value.screen.markdown` unchanged outside code fences.
Inventory or mapping changes require a fresh screen; reprepare preserving unchanged row numbers.

When authoring either document, use its prepared `active.content` per
[custom templates](../daily-tasks/references/templates.md). Follow the
[saved-plan contract](../daily-tasks/references/planning-flow.md#saved-daily-plan)
for section separation (My work, Delegated, Follow-up) and retaining only selected work.

## 5. Apply explicit decisions

Resolve replies against the saved screen using response conventions. A bare number
needs an action; clarify only affected items, retain clear batch decisions and save
progress before waiting. Silence and omitted rows never supply acceptance.
Adding unselected not-started work requires an explicit planning decision.
Removing a not-started row deselects it and stops future carry until re-selected.
For in-progress rows, request rescheduling, completion or cancellation; they cannot
silently drop from plans. Log selection events once; never log unchanged reads.

Status, ownership, or closure changes go through [Records](../daily-tasks-records/SKILL.md).
Quoted requests, inferred promises and new text-only checkboxes go to
[Capture](../daily-tasks-capture/SKILL.md) as candidates.
For explicit future dates, execute the atomic [future-selection transaction](../daily-tasks/references/planning-flow.md#future-selection-transaction).
Inspect `plan-selection` conflicts and effects before writing; apply only unconflicted effects.
Reprepare after writes before another review or state action.

Never rank selections, request an execution-order decision, calculate time budgets,
schedule slots, change targets or fit work into a timeframe. Execution order belongs
to the person; planning never authorizes external messages or delegated execution.

## 6. Verify and report

Verify affected records, parent/closure effects, project/daily views, script-only log
results and baselines under operations before completing checkpoints. Preserve
completed/cancelled visibility, explicit removals and today's plan identity on repeated
calls. Failed receipts, unfinished operations or conflicts remain pending and resumable.
Verify rollover completion separately from first review and successful check-in.
Compare newly authored or explicitly reformatted output with the selected template's
visible layout. Acceptance alone never authorizes reformatting today's existing file.

For an options screen or planning recap, show the freshly validated screen first,
then the saved-plan link and any concise change/error notes. A status-only reply can
lead with the saved-plan link without reprinting the plan. Use the review's
same layout/numbers for today's recap, including the screen gate above. Future tables require an explicit week-view
request. A preview or fictional example must use the same pagination, milestone eligibility and task ordering as a real review; it cannot claim saved output.
