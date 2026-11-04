# Verified operation completion

> [!IMPORTANT] Scope Directive
> This reference owns the Schema Version 2 write-ahead checkpoint specification, selection-transfer state descriptors, rollover receipt structures, and conflict/recovery semantics for verified disk operations. It does NOT own step-by-step workflow checklists (owned by `workflows/*.md`), MCP/CLI invocation syntax (owned by [`cli.md`](cli.md)), high-level write-ahead rationale (owned by [`operations.md`](operations.md)), canonical record schemas (owned by [`records.md`](records.md)), or planning domain rules (owned by [`planning-flow.md`](planning-flow.md)).

## Deterministic verification boundary

In Daily Tasks, caller assertions that an edit is "verified" or "complete" are never accepted as proof of persistence. Whether updates are committed through `daily_tasks_confirm_plan` in the MCP server or verified against a write-ahead checkpoint, completion requires deterministic verification of actual on-disk UTF-8 file contents, append-only decision-log persistence, and baseline synchronization before an operation is marked complete.

## Checkpoint Schema Version 2 specification

Write-ahead checkpoints reside at `stateRoot/operations/<operation-id>.json`. A valid Schema Version 2 checkpoint document contains the following structural fields:
- **`operation_id`**: UUIDv7 uniquely identifying the pending operation.
- **`schemaVersion`**: Literal integer `2`.
- **`contextBinding`**: Opaque hash of the normalized workspace roots ensuring the checkpoint is evaluated only against its originating workspace.
- **`event`**: Structured decision-log entry (`docs/specs/decision-log-entry.json`) to be appended to `<stateRoot>/decision-log.json`.
- **`files`**: Array of declared file effects `[{path: absolutePath, before: SHA256|null, after: SHA256|null}]`, where `null` denotes file absence prior to creation or after retirement. Declared targets must be visible Markdown files inside `projectsRoot` or `dailyPlansRoot`; state files, logs, and symlinks are never valid file effects.
- **`protectedFiles`** *(optional)*: Array of `{path: absolutePath, sha256: SHA256}` assertions verifying that referenced source files remained unmodified during the operation.
- **`baseline`** *(optional)*: Proposed update to `stateRoot/reconciliation.json` structured as `{beforeHash, beforeText, value: {schemaVersion: 1, records: {UUID: {canonical: {...}, views: {...}}}}}`.

## Specialized completion payloads

### Daily plan selection transfers (`selectionState`)

When tasks are explicitly added to, removed from, or moved between dated daily plans (`<dailyPlansRoot>/YYYY.MM.DD-daily-plan.md`), the `selectionState` descriptor tracks both the Markdown plan effect and the per-day `removedIds` deselection set in `stateRoot/rollover/YYYY.MM.DD.json`:
- **Intent structure**: `selectionState: {direction: "add" | "remove" | "move", taskIds: [UUID], source?, destination?}` where `add` specifies `destination`, `remove` specifies `source`, and `move` specifies both `source` and `destination` across distinct dates and plan UUIDs.
- **Endpoint descriptor**: Each `source` or `destination` entry captures `{date: "YYYY.MM.DD", planPath, planId, beforeMarkdown, stateBeforeHash, stateBeforeText}`, recording the exact prior UTF-8 Markdown text and rollover state hash (or `null` when creating a new file).
- **Deselection synchronization**: Completing an `add` or `move` clears the transferred `taskIds` from `removedIds` at the destination date, while `remove` or `move` records the deselected `taskIds` in `removedIds` at the source date so deselected `not-started` tasks are not re-carried automatically. Selection transfers never fabricate rollover completion timestamps (`operationId` and `completedAt` remain unset unless rollover itself ran).

### Daily rollover completion (`rollover`)

When once-per-day carry-forward creates or updates today's daily plan from the nearest preceding daily plan, the `rollover` payload (`{date, planId, previousPlanId, expectedCreatedAt, removedIds, expectedSelectedIds, previousPath, previousHash, expectedStateHash, sourceSnapshot}`) binds the carried task set to the prior plan's hash and canonical record state. Upon verified completion, the dated rollover receipt at `stateRoot/rollover/YYYY.MM.DD.json` records `operationId` and UTC `completedAt`, the decision log entry is appended, the reconciliation baseline is updated, the inventory cache sidecar is invalidated, and the transient checkpoint is removed last.

## Recovery and conflict semantics

Verification evaluates to one of three deterministic outcomes: `verified` (all declared `after` file hashes, protected files, log entries, and owned state match), `pending` (some declared effects have not yet been written to disk), or `conflict` (an intervening edit altered a file's `before` bytes, a protected source, or a baseline record). When an operation is interrupted or reports `pending`, the checkpoint remains on disk so re-running verification resumes idempotently without duplicating decision-log entries. When `conflict` is reported, disk files and the checkpoint remain untouched until the user explicitly adjudicates the conflicting edit.
