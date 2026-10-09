# Context, inventory and planning

The Windows Codex app is the execution host. Phone access uses the same host's
vault, filesystem, Node runtime, skills and timezone. Never infer vault paths or
the phone's timezone from a remote prompt. Do not require a separate server.
Desktop and phone activation require actual host testing, not package checks.

## Resolve once

For routine entry use `planning-prepare` with the captured vault binding and known
profilePath, instead of composing temporary orchestration scripts. Its packet includes
context, current/previous plan identities and hashes, inventory, rollover, review,
pending operations, maintenance gate and explicit enrollment issues. It validates the
complete inventory graph; selected-record fragments are not a validation universe.
Inspect pending/reconciliation issues before applying the proposals. After recovery,
reconciliation, plan or state writes change packet hashes, run planning-prepare again
before a dependent state action or review save; never reuse stale fingerprints.
Preserve saved mapping numbers for unchanged identities when preparing again.
A prepared packet does not mean rollover, reconciliation or check-in has completed.

Omit `now` on initial preparation so the host resolves its actual clock and local
day. Use the returned localDate even when the UTC calendar date differs. A requested
planning date is not a clock override; future selections use `plan-selection`'s
date input. Follow the [CLI clock rules](cli.md) for new event/receipt timestamps
and for preserving original timestamps during recovery.

Capture the host's initial workspace/vault binding once at the start of the request.
For a vault-root workspace, pass that absolute path as `initialCwd` to
`resolve-context`; an already resolved vaultRoot takes precedence. Never use a
changed shell/subprocess cwd as a vault root or derive roots from plugin location.
Pass an established explicit profilePath/configRoot when available; otherwise the
resolver searches vault `.nyssaai/daily-tasks/profile.json` before the home profile.
Reuse legacy explicit profile/state bindings; do not silently migrate them.

The returned context contains resolved absolute roots, templates, identity, actual
timezone, localDate and TTL. Relative profile paths are anchored to the captured
vault; `~/` paths are anchored to the executing user's home. Keep portable paths in
the profile and resolved paths in this request's runtime context. User preferences
may be home-scoped, but stateRoot defaults to the vault's `.nyssaai/daily-tasks` so
different vaults do not share pending operations, baselines or check-in progress.
Use stateRoot for operational state and configRoot for the selected profile/templates.
When configuration is missing/conflicting or explicitly changed, load
[Setup](../../daily-tasks-setup/SKILL.md) for authoritative discovery precedence,
first-use questions and output defaults. Reuse configured scope without restarting
setup; Setup reports the actual detected timezone.

A planning session has exactly one bound vault and one projectsRoot assigned to it.
Home-level preferences can be reused in separate vault sessions; they never widen
the current inventory, numbered replies or record operations to another vault.
An explicitly configured external projectsRoot is storage for this selected vault,
not authorization to search other vaults or merge their inventories. Keep that binding
fixed through follow-up replies and recovery; finish/suspend it before opening a
separate session for a different vault. A multi-vault planning request needs separate
vault sessions, not a combined screen or implicit root switch.

`resolve-context` returns planningBinding, an opaque fingerprint of its normalized
absolute vault/projects/daily-plan roots. For planning-review, plan-selection,
carry-forward and plan-rollover, pass those same three roots plus contextBinding
from that result. When supplying inventory, pass inventoryBinding from project-index's
planningBinding result; do not invent it from a cached file or copy a value between
vaults. The CLI rejects mismatched roots/inventories before producing planning effects.
Bindings are routing checks, not a substitute for filesystem permissions or authority.

## Load and maintain

Call `project-index` with resolved vaultRoot/projectsRoot/dailyPlansRoot, timezone,
TTL and current GMT now. An explicit inventory refresh sets forceRefresh. Cache is
`<vaultRoot>/.temp/daily-tasks/project-index.json`; its separate freshness sidecar is
also disposable. Do not read task contents again when the command reports reused.
Use sourceReads/metadataFiles as cost evidence, not proof of host activation.
Record/source paths remain relative to their anchors. An external root outside both
vault/home is represented as `@projectsRoot`, resolved through this session's context.
The actual root compatibility fingerprint stays in the disposable freshness sidecar.
Never turn the logical anchor into an absolute path in the inventory or persist
computed eligibility/count fields there. Each vault retains its own cache.

Read current plan and the most recent earlier plan when needed, inspect their edits,
and recover applicable pending operations on every request, even with fresh inventory.
Call `maintenance-status` with the resolved context, not a supplied success timestamp.
Its `inspectionDue` gate concerns CLI checks; `fullReconcileDue` remains true when
trusted host worker evidence is unavailable. If inspection is due, optionally run one read-only maintenance subagent
using explicit `gpt-6-luna` on Codex, Haiku on Claude, or another supported lightweight
model. Use the host's actual subagent tool with that model parameter; a Markdown
declaration is not evidence that the model ran. Use `fork_turns: "none"` with Codex
`spawn_agent` so the explicit model override works and unrelated history is omitted.
Pass only resolved roots, relevant plan paths, inventory input and bounded task
instructions with the operation/baseline contract. The worker can call
project-index, inspect records and compare baselines, returning proposals, source
hashes and diagnostics. It must not author canonical Markdown, logs or baseline state.
Do not spawn another worker solely for indexing. If model selection/subagents are
unavailable, report that exact limitation and perform the same checks directly.

The parent reconciles/apply-verifies authorized safe effects; user conflicts remain
in their separate queue. Run `maintenance-inspect` after those changes; it reads the
actual graph, navigation, baselines and pending operations. Only a successful CLI
inspection saves `maintenance-inspection.json`, with its own clock and execution kind.
It never advances a worker-success timestamp. The current CLI has no trusted host
worker-evidence adapter: do not write `maintenance.json`, claim an unavailable model
ran, or turn an inspection into worker-success evidence. Report an unavailable worker
truthfully and preserve previous success. Blocked checks leave inspection state unchanged.
Inventory generatedAt is independent; deleting `.temp` cannot erase inspection evidence.
No worker runs merely because time passes. The gate is checked on requested use.

Inventory view-state-difference diagnostics identify discrepancies, not the winning
edit. Compare each view to its stored baseline with reconcile-record. For a parsed
projection with an explicit state use that state alone; otherwise use checked so
blocker completion translates to resolved and legacy unchecked work stays start-aware.
Legacy unchecked struck-through Cancelled rows normalize to explicit cancelled state,
not completed. Compare that edit with its baseline; never cancel the canonical task
merely because a stale unchanged view still has the old cancellation caption.
Refresh inventory after reconciled writes. Never hide an edit by regenerating its
view before reconciliation. Missing milestone ordering/identities require resolution.
Valid tasks omitted from an index follow its listed tasks by filename for stable
presentation; this is not an execution order and does not block accepted tasks.
Navigation-only links do not need managed IDs. Report unidentified legacy records
as enrollment work, with their paths and missing metadata. Do not assign identities,
owners or states, or accept their checklist candidates without the user's decision.

## Build and review

Before building the review, finish the once-per-day rollover below. An existing
plan, including a future-created one, does not mean rollover has occurred.

Call planning-review with inventory, userEmail, timezone, now, current selected rows,
selectedRecords (canonical parsed records for all current selections, including
terminal rows), and the saved UUID-to-number mapping. Carried rows include carriedFrom.
It returns selected/available rows, counts, hasMore, diagnostics and an updated mapping.
Persist the mapping together with mappingBinding from the result and the local date
in stateRoot before waiting. Pass mappingBinding when reusing a nonempty mapping;
a different binding invalidates the numbered screen, never reinterprets its numbers.
With a preparation packet, use `planning-state` action `save-review` and its current
plan hash, previous-plan hash (null if absent), and state.review.sha256. This rereads
and verifies the actual files and saves the mapping in stateRoot/review/DATE.json.
An existing same-day planning-review.json is reused without discarding its numbers.
Also pass inventoryHash as expectedInventoryHash and reviewHash as expectedReviewHash,
and reuse context.now plus the same page/allMilestones options. A changed inventory or
numbering requires a fresh screen; never silently save different numbers from those shown.
Show more increments page and reuses
that mapping. All-milestones requests set allMilestones without lifting the 15-row cap.
Pending future selections pass pendingFutureIds to suppress repeat suggestions.
Out-of-view selections are preserved in the daily plan, not displayed in this owner view.

Apply templates.planDayReview or the bundled screen. Match its count line, conditional,
six columns (#, Status, Project, Milestone, Task, Due Date), legends, carry marker
and today-only recap. If incomplete is true, add a
short factual note that counts/options are incomplete and route affected diagnostics
to reconciliation; do not add blockers or a Needs clarification section to this screen.
The conditional first_run_today describes the first review run, not plan-file existence
or a pre-created future plan. Completed check-in state is tracked independently.

Commands must include an action and stable numbers. Resolve ambiguous commands before
affected writes; process independent clear items. Status reports update canonical tasks,
parent effects and project views first, daily plan second. They do not select work.
No execution ordering, scheduling/time fitting, implicit acceptance or automatic shortlist.

## Review scope

Load this contract before deriving review rows or inventory counts. The review is
owner-only: canonical owner must match the current user's email, regardless of
assignee. Do not split delegated rows or show assignees, blockers, blocker counts
or a Needs clarification section. Preserve affected selections while reconciliation
handles uncertain facts separately. This filter never removes out-of-view selections
from the saved plan. Ownership permits planning/delegation decisions, not execution.

Counts describe the full user-owned scoped inventory at the recorded update time:
unique open projects/tasks are not-started or in-progress; late tasks are open tasks
with an explicit target_date before the configured local day. Due today is not late.
Never infer dates/counts; identify stale/incomplete inventory rather than claiming
verified exact totals. The addition-page cap does not limit selected rows or counts.

Order projects by directory date, oldest first, with alphabetical name tie-breaking;
undated directories follow alphabetically. Preserve indexed task order, then place
valid unlisted tasks by filename. Missing index links do not make accepted work
ineligible. This is stable presentation, never priority/due-date ranking or execution
order. Show only the first incomplete milestone in authoritative sequence, skipping
completed/cancelled milestones, unless all milestones are explicitly requested.
An empty first incomplete milestone does not advance eligibility to the next.
Resolve unknown sequence before relying on "first"; never use UUID ordering.
Preserve existing selections from later milestones.

Keep selected tasks out of available rows. Exclude explicit future-day selections,
including durable allocations and pending review decisions; a future due date alone
does not exclude a task. Work moved to another day does not return on later pages or
today's recap. Offer at most 15 available additions per page with Show more for the
remainder; all-milestones requests keep this cap. Never make an automatic shortlist.
First review introduction, plan-file existence, rollover completion and successful
check-in are separate states. On resumed/same-day requests preserve the plan and
follow the requested route rather than forcing the first-check-in screen again.

## Saved daily plan

Load this contract when authoring saved output, independently of the owner-only
review. Separate **My work** (effective assignee is current user's email, including
work owned by someone else) from **Delegated work** (owner is current user, effective
assignee is another human/agent). Missing assignee falls back to owner; there is no
unassigned category. Delegated completion belongs to its doer. Suggested follow-up
is a Capture candidate, never a silently created obligation; ownership does not
authorize external messages or taking over execution.

Only selected work belongs in the saved plan; available options/prompts stay on the
review screen. Preserve selections outside its ownership filter, stable display
order, existing prose and terminal/unresolved rows. Do not silently reorder work.
Use the configured dailyPlan template; when supplied, load [custom templates](templates.md)
for authoritative precedence, registration and adaptation. Otherwise use the
[daily-plan asset](../assets/daily-plan.md) for visible layout/placeholders. The
review independently uses planDayReview or its [screen asset](../assets/plan-day-select-tasks-screen.md).
Template examples supply no work acceptance or execution authority.

Use readable task links with hidden UUID refs and one status mark per task (a table
Status cell or the custom template's supported checkbox form). Never expose raw IDs
or repeat full task metadata. When needed, add concise project, delegated assignee
or concrete blocker context. Omit sample/blank rows and unsupplied Focus; use short
empty-state sentences. Blockers are informational, without task checkbox/ref rows.
Completed rows remain checked and cancelled rows visibly marked for today. Do not
infer focus, deadlines, estimates or slots; no scheduling/timeframe fitting.

## Once-per-day rollover

Open/create today's plan with its stable UUID. Read
`stateRoot/rollover/YYYY.MM.DD.json` and recover any applicable pending operation
first. This durable per-vault state is independent of `.temp` and check-in/maintenance
completion. A complete state has `{schemaVersion:1,date,planId,operationId,completedAt}`;
dates use the configured local day and completedAt is GMT. Optional `removedIds`
holds explicitly deselected UUIDs for that day. A state with no completedAt is
pending, not proof of rollover. Invalid state or a plan-ID mismatch requires
recovery/clarification rather than recarrying removed work.

Call `plan-rollover` with today, planId, userEmail, currentRows and that state when
present. A complete result preserves today's rows without reopening history.
If due, find the most recent earlier valid plan filename, reconcile its edits,
read selected canonical records and refresh the inventory as needed. Call again
with previousDate, previousRows, records and inventory. Pass explicit removals
from pending/review decisions as removedIds; never infer deselection merely from
absence in a pre-created future plan.
If `planning-prepare` reports `missing-plan`, allocate the new plan's stable UUID
first; that packet is not a final carry proposal. Call `plan-rollover` with that
UUID and the actual previous date/rows, canonical records, inventory and explicit
removals before checkpointing the selected IDs.

The command proposes a UUID merge: existing rows/prose are preserved, unfinished
personal/delegated rows are carried, terminal and future-selected work is skipped,
and unresolved references stay visible. Carry provenance records previousDate.
Invalid ancestor facts withhold affected additions through `invalid-planning-scope`;
they never turn a later milestone into the first eligible milestone.

Before any changed Markdown, checkpoint the exact source/destination fingerprints,
membership deltas, removal IDs and stable operation/event IDs through the operation
protocol. Merge only the proposed delta into today's configured template. For each
added carried row, render one link using the canonical task title or parsed `label`
and the correctly rebased target. A parsed/carried row's `title` contains full row
presentation, including links and context; do not wrap it inside another link.
Keep the carry marker and assignee context outside the link. For an
existing plan, retain its original id and created_at instead of filling those fields
from template placeholders or the current clock. Compare both saved values to the
checkpoint's before bytes before logging or completing rollover; a mismatch leaves
the operation pending. Verify saved memberships and retained edits, append actual
selection decisions once via the log CLI, invalidate inventory immediately after a committed plan write, then
refresh affected inventory and baselines. A no-change rollover needs no log entry.
For changed rollover use a schemaV2 checkpoint and `rollover-complete` under
[verified completion](verification.md); never write its completion receipt directly.
The CLI rechecks identity, membership, prior/task sources, event and baseline facts.
Only after verification does it write completedAt/operationId into the dated rollover state;
for a no-change pass generate an operation UUID for its completion receipt. A failure
or unresolved carried reference leaves completion pending; persist exact attempted
membership so a later removal is not overwritten during recovery. Re-read and
optimistically compare the state before writing it. Retain the checkpoint until
the completion receipt and all required effects are verified.

For a no-change rollover, `planning-state` action `complete-rollover` generates the
receipt using the actual current plan's UUID, never a caller-supplied parsed record.
Pass expectedPlanHash, expectedPreviousHash and state.rollover.sha256 as
expectedStateHash from preparation. It refuses outstanding operations or membership
deltas; changed-rollover operations still follow the checkpoint/log protocol above.
Use --dry-run to preview either state action. Do not label a failed state write complete.
Pass inventoryHash as expectedInventoryHash and context.now in this action too.

On later same-day calls, preserve manual removals and completed/cancelled visibility;
do not merge yesterday a second time. Recreating a deleted plan with a new ID cannot
silently reuse or reset its receipt. Carry-forward, first-review introduction and
successful check-in completion are separate states.

## Future-selection transaction

Resolve and echo an explicit requested future calendar date in the effective zone.
Use plan-selection with inventory, taskIds, action add/move/remove, date when applicable,
today and dailyPlansRoot. It returns effects and conflicts and writes no Markdown.
Inspect both fields before creating a checkpoint or writing. A successful process
exit does not authorize a change: suspend each conflicted task, preserve its plans
and state, and report the unresolved identity or decision. Apply only returned
unconflicted effects; never reconstruct an effect from the request or a visible row.
An empty effects list authorizes no plan/state write or selection event. Refresh
inventory and resolve the conflict before requesting a new proposal for that task.
Each task has one active planning date; historical rows remain historical. An add
that conflicts with another active date requires clarification; an explicit move
transfers that selection. Removing a selection defaults to today, not another day.

For each authorized effect, read the destination/source and check actual selections
by task UUID. Create a pending operation BEFORE writing, including expected file hashes,
before/after row membership, generated plan ID/timestamps, event ID and all affected paths.
For an absent destination, render the configured dailyPlan template with a new UUIDv7
frontmatter id and GMT creation/update timestamps, actual local date/timezone, real
relative task link/ref, and no sample work or inferred focus. For an existing plan,
preserve its original id and created_at, prose, selections and other people's edits.
Verify those identity fields against the before bytes after writing. Do not mark execution
started/completed, alter target_date or create every intervening day's plan.

Write/verify destination first, then remove the task from its old active day if
different. Preserve earlier historical plans and unrelated rows. Use optimistic
before-hash checks, the operation protocol and script-only log append. If interrupted
after creating the destination, retain the checkpoint and complete the source removal
before planning that task again; don't claim success or collapse duplicate active dates.
Retry with the same plan/operation/event IDs. Recovery never creates a second plan.
Invalidate the inventory sidecar as soon as a plan write commits, even if a later
effect fails; retain the pending checkpoint until the whole transfer is verified.
Within the same checkpoint, update the affected dates' durable rollover removedIds:
remove/move-from adds the UUID; add/move-to clears it. Preserve any completion
receipt already present. When a future plan has no rollover state, initialize a
pending state with its existing plan UUID, never a completed receipt. Verify these
state effects too, so later carry cannot undo an explicit future-day deselection.

After all required effects and log append are verified, run invalidate-project-index,
refresh inventory and verify exactly one intended active date (or none after removal).
Then finish the checkpoint and update per-view baselines. Re-read the current date
before saving if the review crossed midnight; resolve an ambiguous day-relative command.
Recap today using the same layout; future tables require an explicit week-view request.
Verify saved files and log results; a fictional sample/dry run cannot claim persistence.
