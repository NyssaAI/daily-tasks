# Context, inventory and planning

> [!IMPORTANT]
> **Scope Directive**: This document defines the domain logic, lifecycle invariants, review eligibility rules, once-per-day rollover mechanics, and future-day selection transactions for Daily Tasks planning sessions. It is strictly a planning domain specification. Low-level CLI flags and invocation syntax belong in [`cli.md`](cli.md), transactional write-ahead checkpointing and baseline reconciliation in [`operations.md`](operations.md), record schemas in [`records.md`](records.md), and user-facing review screens, table legends, and prompt styles in [`response-conventions.md`](response-conventions.md).

Daily Tasks planning operates within a single bound workspace context and its associated projects, daily plans, and operating state roots.

```text
Daily Tasks Planning Session
│
├── 1. Resolve once (## Resolve once)
│   ├── Bind single workspace context (workspaceRoot, projectsRoot, dailyPlansRoot)
│   ├── Resolve host clock & local day (omit `now` on initial run)
│   ├── Capture opaque routing tokens (planningBinding, contextBinding)
│   └── Isolate operating state in stateRoot (.nyssa-ai/daily-tasks)
│
├── 2. Load & maintain (## Load and maintain)
│   ├── Run project-index (check cache & freshness sidecar in .temp/)
│   ├── Inspect maintenance-status (check inspectionDue gate)
│   └── Scoped diagnostic handling (isolate issues; permit independent planning)
│
├── 3. Once-per-day rollover (## Once-per-day rollover)
│   ├── Check stateRoot/rollover/YYYY.MM.DD.json (run once per day)
│   ├── Propose carry delta via plan-rollover (in-progress work persists, unfinished selections carry)
│   └── Complete transaction (Schema V2 checkpoint or complete-rollover receipt)
│
├── 4. Build & review (## Build and review & ## Review scope)
│   ├── Scoped review filtering (all-owner visibility, lowest incomplete milestone only)
│   ├── Format & paginate review (one project per page, planDayReview template)
│   └── Save review state (planning-state save-review validates draft & mapping)
│
└── 5. Selection & daily plan updates
    ├── Today's selections (## Saved daily plan: My work, Delegated, Follow-up)
    └── Future selections (## Future-selection transaction: atomic move & removedIds sync)
```

## Resolve once

Initialize planning using `planning-prepare` with the captured workspace binding.

### Invariants and lifecycle
- **Single workspace binding**: A planning session binds exactly one workspace root, one `projectsRoot`, and one `dailyPlansRoot`. Do not mix inventories, numbered replies, or record operations across different workspaces.
- **Clock and local day**: Omit `now` on initial preparation to allow the host to resolve its actual clock and local date. Follow host local day even when UTC date differs. A requested planning day is an argument to `plan-selection`, not a clock override.
- **Context bindings**: `resolve-context` issues `planningBinding`, an opaque hash of normalized roots. Subsequent calls to `planning-review`, `plan-selection`, and `plan-rollover` require `contextBinding`, `inventoryBinding`, and (when reusing an active numbered screen) `mappingBinding`. Mismatched roots fail validation before any side effects.
- **State isolation**: Operational state (checkpoints, rollover history, review state) lives in `stateRoot` (`.nyssa-ai/daily-tasks`), strictly isolated per workspace. Home preferences configure defaults but do not share operational state across workspaces.
- **Fresh preparation requirement**: Any write, reconciliation, recovery, or plan edit invalidates prepared hashes. Rerun `planning-prepare` before dependent state actions or review saves; never reuse stale fingerprints.

## Load and maintain

Load and validate workspace project inventory and inspect maintenance status.

### Inventory cache and indexing
- Run `project-index` with resolved roots, timezone, and TTL.
- The inventory cache lives at `<workspaceRoot>/.temp/daily-tasks/project-index.json` with a separate freshness sidecar.
- Relative paths remain anchored to their logical roots; an external projects root outside workspace/home is anchored as `@projectsRoot`.
- When the CLI reports the cache was reused, avoid re-reading task files. Invalidate the inventory cache immediately after any committed plan write.

### Maintenance gate and worker boundary
- Check `maintenance-status` with the resolved context. The `inspectionDue` boolean determines whether CLI maintenance inspection is needed.
- If worker capabilities are unsupported (`workerEvidence.status: "unsupported"`), report this limitation truthfully. Never fabricate worker success evidence or write `maintenance.json`.
- When inspection is due, read-only maintenance checks may run directly or via a lightweight read-only subagent. Maintenance workers must never write canonical Markdown, logs, or baselines.
- Run `maintenance-inspect` following verified changes; only successful CLI inspections update `maintenance-inspection.json`.
- A blocked inspection or non-critical diagnostic (e.g. navigation-only broken link, legacy project enrollment) is scoped evidence: suspend only affected dependent writes, and permit unrelated rollover, review mapping, or plan saves to proceed.

## Build and review

Generate, paginate, and validate the interactive daily review screen.

### Review packet and numbered mapping
- Rollover must be complete before presenting the daily review.
- `planning-review` takes inventory, user email, timezone, selected rows, canonical records, and existing UUID-to-number mapping. It returns scoped counts, selected/available rows, pagination info, and an updated mapping.
- The mapping must be saved to `stateRoot/review/YYYY.MM.DD.json` using `planning-state` action `save-review`.
- Saving requires the complete agent-authored `reviewMarkdown`, current/previous plan hashes, `expectedReviewHash`, and `expectedInventoryHash`. Saving validates draft headings, table columns, task identities, row numbers, statuses, carry markers, and legends against the active `planDayReview` template.
- Resuming a review without an explicit page parameter restores the saved project anchor and pagination state.

### Review rules
- **One project per page**: Display available tasks grouped by project, one project per page. "Show more" advances to the next project.
- **Review complete**: When no further project options remain, indicate review completion rather than an empty page.
- **Draft fidelity**: Display the verified `value.screen.markdown` returned by `save-review` unchanged; fix rejected drafts before prompting the user for choices.

## Review scope

Rules governing task eligibility, ordering, and counts across the scoped inventory.

### Visibility and ownership
- Review covers all valid tasks in the bound `projectsRoot`, regardless of owner or assignee.
- Tasks retain owner and assignee attributes to distinguish personal work, delegated work, and follow-up work.
- Review visibility permits planning and check-in decisions; it does not alter assignment, reassign ownership, or start execution.

### Scoped inventory counts
- **Open tasks**: Tasks in `not-started` state with no future-day allocation or pending selection.
- **In-progress tasks**: Tasks with ongoing execution; counted separately from new options.
- **Open projects**: Unfinished projects containing at least one open task.
- **Late tasks**: Open tasks with an explicit `target_date` prior to the configured local day (`due today` is not late).
- Do not fabricate counts; report incomplete or unindexed inventory explicitly.

### Ordering and milestone eligibility
- **Project ordering**: Projects are ordered by directory date (oldest first), with alphabetical name tie-breaking; undated directories follow alphabetically.
- **Milestone eligibility**: Tasks from all incomplete milestones (`not-started` or `in-progress`) in a project are eligible for selection, presented in authoritative milestone sequence (`M1`, then `M2`, `M3`, …). Completed and cancelled milestones are skipped. Existing selections from any milestone remain valid.
- **Task ordering**: Tasks appear in canonical index order, followed by unlisted valid tasks sorted by filename. This order is a stable display sequence, not a priority or execution order.
- **Available tasks**: Only unselected open tasks appear in the available section. In-progress and already-selected tasks are excluded from available options. Explicit future-day allocations are excluded from today's available options.

## Saved daily plan

Requirements and content structure for the persisted daily plan document.

### Section separation
- Categorize selections into:
  - **My work**: Effective assignee matches current user email (including work owned by others).
  - **Delegated work**: Current user is owner; effective assignee is another person or agent.
  - **Follow-up work**: Both owner and effective assignee are third parties.
- Unassigned tasks fall back to their owner.
- Suggested follow-up is capture candidate material; it is never converted into an implicit obligation.

### Document structure
- **Template layout**: Follow `packet.templates.templates.dailyPlan.active.content` for headings (`# Daily plan — LOCAL_DATE`, `## Selected for today`, `### My work`, `### Delegated work`, `### Follow-up work`, `## Blockers`, `## Decisions`, `## Notes and references`), counts (`Open projects: ... Open tasks: ... Late tasks: ...`), `**Timezone:**`, `**Updated:**`, `#### PROJECT_TITLE / MILESTONE_TITLE` group subheadings, 6-column tables (`| # | Status | Project | Milestone | Task | Due Date |`), and `Legend:`. Never replace table rows with `- [ ]` bullet lists unless the active `dailyPlan` template uses checklists.
- **Task link presentation**: Always provide the human-readable task title as the display label (`[[relative-path\|Task title]] <!-- ref: UUID -->`, escaping the wiki-link pipe inside table cells). Prefix carried items with `↺ ` outside the wiki link. Never expose raw filesystem paths or bare UUIDs to the user.
- Represent status using single status indicators matching the active template (`[ ]`, `[>]`, `[x]`, `[-]`).
- Completed tasks remain checked and cancelled tasks remain marked for today.
- Only selected work belongs in the plan; available options and interactive prompts stay in the review screen. Use short empty-state sentences for empty sections and omit `## Focus` unless explicitly supplied.
- Never add automatic scheduling, timeframe fitting, duration estimates, or focus tags unless explicitly provided.

## Once-per-day rollover

Deterministic carry-forward of active work from the most recent prior plan into today's plan.

### State and receipt invariants
- Rollover state is tracked at `stateRoot/rollover/YYYY.MM.DD.json`.
- A completed state requires `{ schemaVersion: 1, date, planId, operationId, completedAt }` where `date` is the local day and `completedAt` is GMT ISO.
- `removedIds` tracks explicitly deselected UUIDs for that day to prevent unwanted recarrying.
- Rollover runs exactly once per calendar day. Subsequent runs on the same day preserve manual edits and removals without re-merging prior days.

### Carry-forward rules
- **In-progress persistence**: Every valid in-progress task in the inventory must carry forward into today's plan, even if absent from yesterday's plan or previously deselected, until explicitly marked completed, cancelled, or rescheduled.
- **Unfinished selections**: Carried unfinished tasks from the previous plan receive carry provenance (`carriedFrom: previousDate`) and the carry marker (`↺`).
- **Terminal and future exclusion**: Completed, cancelled, and future-allocated tasks do not carry forward.
- **Unresolved records**: Unresolved or missing task identities remain visible in the plan to avoid silent data loss.

### Execution transaction
1. Use the pre-computed `packet.rollover` and `packet.drafts` from `planning-prepare` (which includes `dailyPlanMarkdown`, `reviewMarkdown`, `rolloverOperation`, `completeRolloverInput`, and `saveReviewInput`).
2. For an existing plan, preserve its original `id` and `created_at` frontmatter. For a missing plan, use `packet.current.proposedId` and `packet.context.now` (`packet.displayNow` for display).
3. If changes are proposed (or a missing plan is created):
   - Write `packet.drafts.rolloverOperation.checkpoint` to `packet.drafts.rolloverOperation.operationPath` and write `packet.drafts.dailyPlanMarkdown` to `packet.current.path`.
   - Finalize in one call via `rollover-complete` using `packet.drafts.rolloverOperation.completeInput` (`validatePlanTemplate: true`, `appendEvent: true`, `prepareNext: true`, `saveReview: true`), which validates the plan layout, appends the `plan.rollover` event, completes the receipt, invalidates the cache, saves the first review screen, and returns `reviewSaved.value.screen.markdown`.
4. If no changes are needed on an existing plan:
   - Finalize the rollover receipt and save the review screen in one call via `planning-state` using `packet.drafts.completeRolloverInput` (`action: "complete-rollover"`, `saveReview: true`).

## Future-selection transaction

Protocol for scheduling tasks for explicit future dates.

### Proposal and conflict check
- Request proposals via `plan-selection` with target `date`, action (`add`, `move`, `remove`), `taskIds`, and resolved context.
- `plan-selection` evaluates date validity, suspended records, and conflicting active selections without modifying Markdown.
- If conflicts exist, suspend affected items, preserve existing plans, and report the conflicts. Apply only unconflicted effects.

### Atomic multi-plan update
- Each task has exactly one active planning date.
- **Move transaction**:
  1. Write and verify the target destination plan first.
  2. Remove the task from the source plan.
  3. Finalize in one call via `operation-complete` (`appendEvent: true`, `prepareNext: true`), which updates `removedIds` in both affected dated rollover states (`add` clears the ID at destination; `remove`/`move-from` records the ID at source), appends the selection event to the decision log, invalidates the inventory cache, and completes the checkpoint.
- If interrupted, the write-ahead checkpoint ensures source removal and state cleanup resume deterministically without creating duplicate active dates or duplicate plans.
