# Verified operation completion

> [!IMPORTANT]
> **Scope Directive**: This document defines the verification contracts, Schema Version 2 checkpoint structures, baseline assertions, and state completion requirements evaluated by `operation-verify`, `operation-complete`, and `rollover-complete`. It is strictly a verification and completion engine specification. Low-level CLI commands and signatures belong in [`cli.md`](cli.md), overall write-ahead operational workflows in [`operations.md`](operations.md), record schemas in [`records.md`](records.md), and planning/rollover domain rules in [`planning-flow.md`](planning-flow.md).

The agent authors Markdown files and records checkpoints; the CLI deterministically verifies actual disk contents, checks log events via the log API, writes updated baselines, and clears checkpoints. Caller assertions of "verified" or "complete" are never accepted as proof.

## Checkpoint Schema Version 2 contract

Checkpoints reside at `stateRoot/operations/<operation-id>.json`. Every Schema Version 2 checkpoint requires:
- `operation_id`: UUIDv7 identifying the operation.
- `schemaVersion`: Literal integer `2`.
- `contextBinding`: Opaque normalized workspace root hash matching `resolve-context`.
- `event`: Exact log entry object to be recorded via `log-append`.
- `files`: Declared file effects `[{path: absolutePath, before: SHA256|null, after: SHA256|null}]`.
  - `null` represents file absence (new file created or retired file deleted).
  - Target paths must be visible Markdown files within `projectsRoot` or `dailyPlansRoot`.
  - State files, log files, and symlinks cannot be declared as file effects.
- `protectedFiles` (optional): `[{path: absolutePath, sha256: SHA256}]` asserting unchanged sources.
- `baseline` (optional): Proposed update to `stateRoot/reconciliation.json`:
  `{beforeHash, beforeText, value: {schemaVersion: 1, records: {UUID: {canonical: {...}, views: {...}}}}}`.

## Specialized completion intents

### 1. Daily plan selection transfers (`selectionState`)
Used for explicit task selection adds, removals, or moves across daily plans via `operation-complete`:
- **Intent payload**:
  `selectionState: {direction: "add" | "remove" | "move", taskIds: [UUID], source?, destination?}`
  - `add`: Requires `destination` only.
  - `remove`: Requires `source` only.
  - `move`: Requires both `source` and `destination` (distinct dates and plan UUIDs).
- **Source / Destination descriptor**:
  `{date: "YYYY.MM.DD", planPath, planId, beforeMarkdown, stateBeforeHash, stateBeforeText}`
  - `planPath`: Strictly `<dailyPlansRoot>/YYYY.MM.DD-daily-plan.md`.
  - `beforeMarkdown`: Exact UTF-8 text before edit (or `null` for new destination).
  - `stateBeforeHash` / `stateBeforeText`: Exact prior bytes/hash of `stateRoot/rollover/YYYY.MM.DD.json` (or `null` if file did not exist).
- **Rollover state synchronization**:
  - The CLI derives updated `removedIds` in `stateRoot/rollover/YYYY.MM.DD.json`: destination clears `taskIds`; source adds `taskIds`.
  - Selection changes never fabricate or claim rollover completion (`operationId` and `completedAt` remain unset).
- **Verification execution**:
  `operation-verify` evaluates `persistedStatus` (Markdown effects, protected sources, and log event) and `ownedState` (pending rollover/baseline updates). `operation-complete` writes the owned state, verifies all evidence, and deletes the checkpoint last.

### 2. Daily rollover completion (`rollover`)
Used for carrying forward unfinished work into today's plan via `rollover-complete`:
- **Payload extension**: Includes `rollover` object:
  `{date, planId, previousPlanId, expectedCreatedAt, removedIds, expectedSelectedIds, previousPath, previousHash, expectedStateHash, sourceSnapshot}`
- **Validation**:
  - The CLI independently recomputes carry-forward facts from canonical records and verifies against the nearest preceding daily plan.
  - On success, finalizes the dated receipt (`stateRoot/rollover/YYYY.MM.DD.json`) with `operationId` and GMT `completedAt`, saves the updated baseline, and deletes the checkpoint.

## Failure and recovery rules

- **Inspect structured output**: An exit code of zero indicates process success, not verified completion. Always inspect the returned `status` (`verified`, `pending`, `conflict`).
- **Idempotent resumption**: If an operation is interrupted or returns `pending`, the checkpoint remains on disk. Re-invoking completion with the same checkpoint resumes safely without duplicating log entries or re-applying already-applied state.
- **Conflicts**: Any unexpected modification to declared before-bytes, protected sources, or baseline records produces a `conflict` status. The CLI leaves the checkpoint and disk files untouched for explicit caller reconciliation.
