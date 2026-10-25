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

**Daily plan gate:** Every newly created or updated `YYYY.MM.DD-daily-plan.md` file must
match `packet.templates.templates.dailyPlan.active.content` (by default: `# Daily plan — LOCAL_DATE`,
`Open projects: ... Open tasks: ... Late tasks: ...`, `**Timezone:**`, `**Updated:**`,
`## Selected for today` with `### My work`, `### Delegated work`, and `### Follow-up work`,
`#### PROJECT_TITLE / MILESTONE_TITLE` subheadings, 6-column tables
`| # | Status | Project | Milestone | Task | Due Date |` with escaped wiki-link pipes
`[[relative-path\|Task title]] <!-- ref: UUID -->`, `Legend:`, `## Blockers`, `## Decisions`,
and `## Notes and references`). Never replace the template's tables with a `- [ ]` bullet
checklist unless the active `dailyPlan` template explicitly uses checklists. Both `rollover-complete` and `planning-state` `save-review` validate the daily plan against
the active `dailyPlan` template and reject non-conforming layouts.

**Fast-path execution (start here — no `--help`, no reference/source reads):**
1. **Do NOT run `--help`, do NOT read `src/`, `test/`, or `scripts/`, and do NOT read `references/*.md` (`cli.md`, `planning-flow.md`, `operations.md`, `response-conventions.md`) before running `planning-prepare`.** Resolve `<PLUGIN_ROOT>` as two directories above this `SKILL.md` (`<PLUGIN_ROOT>/src/cli/daily-tasks.mjs`).
2. **Always pass `Overwrite: true`** when writing any `.temp/daily-tasks/*.json` file so leftover files from prior sessions never fail.
3. **Call 1 (`planning-prepare`)**: Write `{"vaultRoot": "<workspaceRoot>"}` (with `Overwrite: true`) to `<workspaceRoot>/.temp/daily-tasks/prep-input.json` and run:
   `node "<PLUGIN_ROOT>/src/cli/daily-tasks.mjs" planning-prepare --input "<workspaceRoot>/.temp/daily-tasks/prep-input.json" --output "<workspaceRoot>/.temp/daily-tasks/prep.json"`
   When `--output` is passed, the CLI automatically writes `<workspaceRoot>/.temp/daily-tasks/prep-summary.json` (compact summary + `drafts`) and the pre-built input files (`rollover-complete-input.json`, `complete-rollover-input.json`, `save-review-input.json`).
4. **Read `<workspaceRoot>/.temp/daily-tasks/prep-summary.json`** (not the full `prep.json`). When `pendingOperations` is empty and `shouldOfferTemplates` is `false`, execute **Call 2** immediately:
   - **If `drafts.rolloverOperation` is non-null**: Write `drafts.rolloverOperation.checkpoint` to `drafts.rolloverOperation.operationPath` (`Overwrite: true`), write `drafts.dailyPlanMarkdown` to `drafts.rolloverOperation.planPath` (`Overwrite: true`), and run:
     `node "<PLUGIN_ROOT>/src/cli/daily-tasks.mjs" rollover-complete --input "<workspaceRoot>/.temp/daily-tasks/rollover-complete-input.json" --output "<workspaceRoot>/.temp/daily-tasks/done.json"`
     Then display `done.json`'s `reviewSaved.value.screen.markdown` unchanged!
   - **Else if `drafts.completeRolloverInput` is non-null**: Run:
     `node "<PLUGIN_ROOT>/src/cli/daily-tasks.mjs" planning-state --input "<workspaceRoot>/.temp/daily-tasks/complete-rollover-input.json" --output "<workspaceRoot>/.temp/daily-tasks/done.json"`
     Then display `done.json`'s `reviewSaved.value.screen.markdown` unchanged!
   - **Else (`rolloverStatus === "complete"`)**: Run:
     `node "<PLUGIN_ROOT>/src/cli/daily-tasks.mjs" planning-state --input "<workspaceRoot>/.temp/daily-tasks/save-review-input.json" --output "<workspaceRoot>/.temp/daily-tasks/done.json"`
     Then display `done.json`'s `value.screen.markdown` unchanged!
5. **When the user asks for "Next page" / "Show more" / "Previous page"**: Write `{"vaultRoot": "<workspaceRoot>", "page": <0-based target page>}` (`Overwrite: true`) to `prep-input.json`, run `planning-prepare --input ... --output prep.json`, then run `planning-state --input save-review-input.json --output done.json` and display `done.json`'s `value.screen.markdown` unchanged.
6. **When the user adds or removes tasks for today (e.g. "Add 7, 8 to today")**: Write `{"vaultRoot": "<workspaceRoot>", "selection": {"action": "add", "taskIds": ["<uuid>", ...], "originalWords": "..."}}` (`Overwrite: true`) to `prep-input.json`, run `planning-prepare --input ... --output prep.json`, write `drafts.selectionOperation.checkpoint` to `drafts.selectionOperation.operationPath` (`Overwrite: true`) and `drafts.selectionOperation.dailyPlanMarkdown` to `drafts.selectionOperation.planPath` (`Overwrite: true`), then run `operation-complete --input selection-complete-input.json --output done.json` and display `done.json`'s `reviewSaved.value.screen.markdown` unchanged.

## 1. Resolve and prepare

Consult [context and planning flow](../daily-tasks/references/planning-flow.md#resolve-once)
only if workspace binding is ambiguous. Reuse the configured profile and
already-loaded guidance. Use [Setup](../daily-tasks-setup/SKILL.md) only for unresolved
settings or an explicit configuration change; do not restart setup for a configured user.
Bind one workspace, its assigned projectsRoot and dailyPlansRoot throughout this session,
numbered replies and recovery. Shared preferences never combine workspaces.

Start with `planning-prepare`, passing the captured absolute workspace binding and
`--output <workspaceRoot>/.temp/daily-tasks/prep.json` (never shell `>` redirection). On
continuation preserve configurationSources, preferenceOverrides and stateRoot from
the accepted context. `planning-prepare` resolves actual dated plan identities/hashes,
`current.proposedId` (for a missing plan), `displayNow`, full-graph inventory,
pre-computed `rollover` (including `selected`, `own`, `delegated`, `followUp`,
`unresolved`, and `taskSources`), pre-computed `review` (including carried selections
and stable numbering), `templates`, ready-to-use `drafts` (`dailyPlanMarkdown`,
`reviewMarkdown`, `rolloverOperation`, `completeRolloverInput`, `saveReviewInput`),
`pendingOperations`, `maintenance`, and `enrollment`
issues in one call. Use this packet directly instead of running separate `resolve-context`,
`template-prepare`, `project-index`, `new-id`, `format-time`, `plan-rollover`, or
`planning-review` calls. Selected records alone are not the validation universe.
Preparation does not reconcile edits, complete rollover or finish check-in.

Use the packet's `context.localDate`, `displayNow`, and actual resolved `context.timezone`.
Consult the [CLI](../daily-tasks/references/cli.md) only if an unusual operation is needed; identify the actual
local zone in the heading and rendered times, never the profile value `"system"`.
Daily output is `<workspaceRoot>/<dailyPlansRelative>/YYYY.MM.DD-daily-plan.md`, normally
`daily-plans`, resolved from the profile. Never use configRoot, operating
state or a later cwd as output. Setup resolves its known default; ask only if
scope remains unknown or points into configuration/state storage.

When `shouldOfferTemplates` is `false` (`templates` have
no unbaselined observations or pending update offers), proceed
without reading [template updates](../daily-tasks/references/template-updates.md) or calling `template-state`. Otherwise retain an observed baseline, offer relevant
changes and continue with the active layout while an update is undecided. Saved-plan and
chat-review choices are independent.

## 2. Recover and reconcile

When `pendingOperations` is empty and no manual
edits or conflicts are reported in `recovery` or `review.diagnostics`, skip directly to
Step 3 without reading [operations](../daily-tasks/references/operations.md) or [record conventions](../daily-tasks/references/records.md), re-reading task files, or querying the decision log. Otherwise load [operations](../daily-tasks/references/operations.md) and [record conventions](../daily-tasks/references/records.md), inspect
current-plan edits and per-view baselines, and recover applicable pending operations before
applying affected changes. Preserve unresolved references instead of guessing identity.

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
and unrelated view differences remain maintenance work; they
do not block independent rollover, review mapping or plan saves whose selected and
carried records validate. Suspend only a proposed write that depends on the affected
record or view, and report the remaining maintenance scope separately.

After reconciled writes, invalidate/refresh affected inventory and run
`planning-prepare` again. Any write changing the packet's source or state hashes
requires a fresh packet before a dependent state action or review is saved.

## 3. Verify rollover

Apply [once-per-day rollover](../daily-tasks/references/planning-flow.md#once-per-day-rollover)
using the pre-computed `packet.rollover` and `packet.drafts` from `planning-prepare`:
- Preserve an existing plan's UUID (`current.id`), original `created_at`, selections, prose and valid edits.
- For a missing plan (`status: "create-plan"`) or when rollover changes today's plan (`packet.drafts.rolloverOperation` is non-null):
  1. Write `packet.drafts.rolloverOperation.checkpoint` as JSON to `packet.drafts.rolloverOperation.operationPath`.
  2. Write `packet.drafts.dailyPlanMarkdown` to `packet.current.path` (which is already formatted to match `templates.templates.dailyPlan.active.content`, with `### My work`, `### Delegated work`, `### Follow-up work`, `#### PROJECT / MILESTONE` subheadings, 6-column tables, and `↺ ` carry markers).
  3. Write `packet.drafts.rolloverOperation.completeInput` to `<workspaceRoot>/.temp/daily-tasks/rollover-complete.json` and run `rollover-complete` (which already sets `validatePlanTemplate: true`, `appendEvent: true`, `prepareNext: true`, and `saveReview: true`). This validates the daily plan, logs `plan.rollover`, writes the rollover receipt, saves the first review screen, and returns `reviewSaved.value.screen.markdown` in one call!
- If today's plan already exists and `rollover` requires no membership change (`packet.drafts.completeRolloverInput` is non-null), write `packet.drafts.completeRolloverInput` to `<workspaceRoot>/.temp/daily-tasks/state-input.json` and run `planning-state` (which completes the rollover receipt and saves the review screen in one call, returning `reviewSaved.value.screen.markdown`).

## 4. Render and save the review mapping

Consult [review scope](../daily-tasks/references/planning-flow.md#review-scope),
[durable mapping](../daily-tasks/references/planning-flow.md#build-and-review)
and [response conventions](../daily-tasks/references/response-conventions.md) when
interpreting numbered replies or custom formatting. Scoped review presents all-owner visibility,
stable ordering, lowest incomplete milestones, and one project per page.

When Step 3 ran `rollover-complete` (or `complete-rollover`) with `saveReview: true`,
the validated screen is already returned in `reviewSaved.value.screen.markdown` — display
`reviewSaved.value.screen.markdown` unchanged outside code fences without running another
`planning-state` call.
When rollover was already complete (`packet.rollover.status === "complete"`), pass
`packet.drafts.saveReviewInput` (which contains `packet.drafts.reviewMarkdown` matching
`packet.templates.templates.planDayReview.active.content`) to `planning-state` and display
`value.screen.markdown` unchanged outside code fences.
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
For adding or removing today's selections, pass `selection: { action: "add" | "remove", taskIds: [...], originalWords: "...", nextPage?: number }` to `planning-prepare` to receive `drafts.selectionOperation`, write `drafts.selectionOperation.checkpoint` to `drafts.selectionOperation.operationPath` and `drafts.selectionOperation.dailyPlanMarkdown` to `drafts.selectionOperation.planPath`, and run `operation-complete` with `drafts.selectionOperation.completeInput` (`appendEvent: true`, `prepareNext: true`, `saveReview: true`), which logs the event, updates the baseline and rollover state, invalidates the cache, saves the updated review screen, and returns `reviewSaved.value.screen.markdown` in one call.

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
