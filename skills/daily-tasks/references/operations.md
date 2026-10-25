# Applying and reconciling changes

> [!IMPORTANT]
> **Scope Directive**: This document defines the transactional write-ahead protocol, checkpoint lifecycle, and baseline reconciliation mechanics for all consequential Markdown modifications. It is strictly an operational integrity specification. Domain record definitions, schemas, planning flows, and CLI flag syntax belong in their respective references (`records.md`, `planning-flow.md`, `cli.md`).

The calling skill authors Markdown; deterministic JS tools validate integrity and baselines.

Keep the active workspace/projects/daily-plan binding fixed. Validate checkpoint paths against this context: canonical/project views belong to `projectsRoot`, daily views to `dailyPlansRoot`, and operating state to `stateRoot`. Checkpoints for other bindings must remain suspended for their respective workspace sessions; never widen active roots or search another workspace to resolve an ID. Include `planningBinding` in new checkpoints.

## Consequential change protocol

Follow this 5-step protocol before any consequential Markdown write or recovery:

### 1. Inspect baselines and records
- Read relevant records and stored per-view baselines from `stateRoot/reconciliation.json`.
- Validate identities, frontmatter, and reciprocal links using CLI tools.
- Surface duplicate or missing records as conflicts and suspend affected work; continue unrelated items.
- Unidentified checkboxes encountered in source text become capture candidates, never fabricated task IDs.

### 2. Write-ahead checkpoint
- Save a pending operation file at `stateRoot/operations/<operation-id>.json` **before** modifying any Markdown file.
- Use Schema Version 2: include UUIDv7 `operation_id` and `event_id`, declared file targets, expected before/after content hashes, typed intent, actor, and GMT timestamps.
- Checkpoints are transient recoverable write-ahead receipts, not permanent logs. Retain original event IDs and timestamps across retries.

### 3. Compare and apply Markdown deltas
- Re-check current file contents against expected `before` hashes immediately before writing.
- Apply status and metadata changes in strict order:
  1. Canonical task documents and required parent effects (milestones/projects).
  2. Project view projections.
  3. Daily-plan view projections.
- If an earlier effect fails, retain the checkpoint and stop; never apply partial downstream projections. Write only agreed deltas; preserve existing prose and unrelated fields.

### 4. Verify, log, and complete in one call
- Propose updated per-view baselines in the checkpoint.
- Execute `operation-complete` (or specialized `rollover-complete`) with `appendEvent: true` (and `prepareNext: true` when continuing a planning session).
- In a single call, the CLI verifies actual file contents, appends the checkpoint's event to the write-only decision log, writes verified baseline state to `stateRoot/reconciliation.json`, invalidates the project-index freshness sidecar, removes the checkpoint file, and (when `prepareNext: true`) returns the refreshed `prepared` planning packet.
- Never manually delete a checkpoint file or advance a baseline when verification returns pending or conflict. (`log-append` and `operation-verify` remain available for standalone or read-only checks.)

## Reconciliation and conflict resolution

- **Baseline structure**: Minimal reconciliation state in `stateRoot/reconciliation.json` tracks canonical fields, last-rendered projection fields, and file fingerprints keyed by record UUID.
- **Normalization**: Compare changed views against that view's prior snapshot, normalized against the canonical baseline. Unchanged stale fields contribute no edit, preventing a stale unchecked box from inadvertently reopening a completed task.
- **Independent field edits**: Safe changes to distinct fields are merged.
- **Conflicting field edits**: Conflicting edits to the same field preserve both values as a durable conflict requiring explicit user resolution. Do not silently overwrite edits using file modification times.
- **Lock recovery**: If a process terminates mid-operation leaving an active `.lock` directory, verify the owning process has exited before removing only that specific lock directory.
