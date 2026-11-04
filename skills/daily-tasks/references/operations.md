# Applying and reconciling changes

> [!IMPORTANT] Scope Directive
> This reference owns the transactional write-ahead philosophy, checkpoint lifecycle model, and baseline reconciliation theory for consequential Markdown modifications. It does NOT own step-by-step record or check-in execution checklists (owned by [`../workflows/records.md`](../workflows/records.md) and [`../workflows/checkin.md`](../workflows/checkin.md)), domain record schemas (owned by [`records.md`](records.md)), planning domain rules (owned by [`planning-flow.md`](planning-flow.md)), or MCP/CLI invocation syntax (owned by [`cli.md`](cli.md)).

## Transactional integrity model

Daily Tasks separates qualitative Markdown authoring from deterministic integrity verification. When changes are applied through the MCP planning session (`daily_tasks_confirm_plan`), `MarkdownFileStore` performs surgical Concrete Syntax Tree (CST) updates, renders the daily plan, and appends to `<stateRoot>/decision-log.json` atomically after explicit user confirmation. When skills author or repair Markdown records outside a planning confirmation, the write-ahead checkpoint and baseline model guarantees that interrupted edits, concurrent manual changes, and multi-file projection updates never leave workspace records in a silently inconsistent state.

Every consequential operation is scoped to a single bound workspace context (`workspaceRoot`, `projectsRoot`, `dailyPlansRoot`, and `stateRoot`). Canonical project and task records belong under `projectsRoot`, dated daily plans belong under `dailyPlansRoot`, and operational state lives under `stateRoot` (`.nyssa-ai/daily-tasks`). Checkpoints created for another workspace binding remain suspended until that workspace is active; an operation never widens active roots or searches across workspaces to resolve an entity UUID.

## Write-ahead checkpoint lifecycle

Before modifying any tracked Markdown record or view outside an in-memory MCP session, the operation model establishes a recoverable write-ahead checkpoint at `stateRoot/operations/<operation-id>.json` using Schema Version 2 (detailed in [`verification.md`](verification.md)). The checkpoint records a UUIDv7 `operation_id` and `event_id`, the `planningBinding` context token, declared file targets with expected `before` and `after` SHA-256 content hashes, typed intent, actor identity, and UTC timestamps. Checkpoints act as transient write-ahead receipts rather than a permanent audit log, retaining their original event IDs and timestamps across recovery retries so interrupted operations remain idempotent.

When applying Markdown deltas, file contents are compared against expected `before` hashes immediately prior to writing. Ordering matters because projections depend on canonical state: canonical task documents and required parent effects (milestones and projects) are updated first, followed by project index views, and finally daily-plan view projections. If an earlier write fails or encounters an unexpected file hash, the checkpoint is retained on disk and downstream projections are halted so partial edits never overwrite newer user prose.

Once the declared Markdown writes complete, verification compares the actual disk contents against the checkpoint's declared `after` hashes, appends the decision event to the write-only decision log, writes the updated per-view baseline to `stateRoot/reconciliation.json`, invalidates the project-index freshness sidecar, and removes the completed checkpoint file last. A checkpoint is never deleted and a baseline is never advanced while verification reports a pending or conflicting state.

## Baseline reconciliation and conflict resolution

Because Markdown records and daily plans are user-editable files, users frequently check off tasks, edit titles, or add notes directly in their editor between sessions. The reconciliation model tracks minimal per-view baselines in `stateRoot/reconciliation.json`, recording canonical fields, last-rendered projection fields, and file fingerprints keyed by record UUID.

When inspecting manual edits, each modified view is compared against its own prior baseline snapshot normalized against the canonical record state. Fields that remain unchanged relative to that view's snapshot contribute no delta; this normalization prevents an older, un-refreshed unchecked box in a secondary view from inadvertently reopening a task that was completed elsewhere.

Independent edits to distinct fields merge cleanly into the canonical record. When two views or an intervening manual edit modify the same field to incompatible values, both values are preserved as a durable conflict for explicit user adjudication. Modification timestamps (`mtime`) are never used to silently pick a winner, and unidentified checkboxes added in prose become capture candidates rather than fabricated task UUIDs. If an interrupted process leaves a stale `.lock` directory behind, lock recovery verifies that the owning process ID has exited before removing only that specific lock directory.

## Out-of-band credential isolation

Credentials and authentication tokens are strictly excluded from the write-ahead checkpoint and reconciliation model. Secrets never enter Markdown records, checkpoints, the decision log, JSON profiles, or chat transcripts. Out-of-band secret capture (`daily_tasks_capture_secret` or `python -m daily_tasks.auth.secret`) writes exclusively to the keyring-protected configuration store and returns a metadata receipt without generating a checkpoint or decision-log entry.
