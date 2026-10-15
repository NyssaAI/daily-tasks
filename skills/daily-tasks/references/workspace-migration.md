# Migrate an existing milestone workspace

> [!IMPORTANT]
> **Scope Directive**: This document defines the protocol for migrating legacy milestone workspaces to current standards (embedding standalone Definition of Done files into milestones, upgrading task/milestone records to `record_version: 2`, and restructuring project directories into standard layouts). It is strictly a migration procedure specification. Low-level CLI commands and signatures belong in [`cli.md`](cli.md), general write-ahead checkpointing and reconciliation in [`operations.md`](operations.md), checkpoint completion rules in [`verification.md`](verification.md), and record schemas in [`records.md`](records.md).

Migration is an explicit, skill-owned Markdown operation. Plugin installation or updates never trigger automatic migration. The CLI validates preconditions and retires legacy references; it does not rewrite or delete user files directly.

## Pre-migration inspection and reconciliation

1. **Reconcile baselines**: Inspect the target milestone, standalone DoD file, child tasks, backlinks, and existing per-view baselines in `stateRoot/reconciliation.json`. Reconcile uncommitted manual edits before migrating.
2. **Path and numbering audit**:
   - Inventory all affected files, attachments, and navigation links.
   - Reuse existing milestone and task numbers when unambiguous; allocate unused positive integers via `next-record-number` if unassigned.
   - On Windows, compare paths case-insensitively. Path collisions or duplicate UUIDs are conflicts that halt migration; legacy records remain untouched until resolved.

## Milestone and task upgrade contract

1. **Embed milestone DoD**:
   - Copy existing standalone DoD criterion text, checked states, and unique criterion UUID comments (`<!-- id: UUIDv7 -->`) into the milestone's embedded `## Definition of Done` section.
   - Retain the milestone's scalar frontmatter, lifecycle state, owner, assignee, and timestamps.
   - If both standalone and embedded criteria already exist, resolve contradictory authority explicitly before modifying files.
2. **Upgrade to `record_version: 2`**:
   - Milestone and task records must include scalar `record_version: 2` and hide parent IDs (`project_id`, `milestone_id`) in frontmatter.
   - Retain existing task-specific criteria. Never fabricate checked criteria from completed status; unaccepted legacy tasks remain unversioned pending user acceptance.
   - Unsatisfied newly-accepted criteria on completed tasks require explicit reopening via `reopen-ancestors`.

## Filesystem restructuring

- **Directory layout**: Ensure task files sit directly inside the milestone directory beside the milestone Markdown file (not nested inside task subfolders).
- **Holding areas**: Create flat `inputs/` and `outputs/` folders beside the milestone file. Move task attachments and deliverables into these folders and link them from task records. Shared assets are referenced in place; never duplicate files per task.

## Checkpoint, retirement, and completion protocol

Follow the 5-step operational protocol with migration-specific gates:

1. **Write-ahead checkpoint**:
   - Save Schema Version 2 checkpoint at `stateRoot/operations/<operation-id>.json` declaring all before/after file bytes, hashes, and retiring paths under the `migration` intent.
   - Keep backup before-bytes in the project's `.temp/` directory (excluded from record discovery).
2. **Apply Markdown updates**:
   - Write updated milestone and task files.
   - Retarget live links pointing to the retired standalone DoD file to the milestone's `## Definition of Done` heading (`[[m1-milestone#Definition of Done|Milestone DoD]] <!-- ref: MILESTONE_UUID -->`).
   - Criteria references retain their original criterion UUIDs.
   - Transfer any blocker relationships targeting the standalone DoD to the milestone file.
3. **Pre-retirement validation gate (`migration-retirement`)**:
   - Run `migration-retirement` **while the standalone DoD file still exists**.
   - If `allowed: false` is returned (e.g. unmigrated criteria or remaining live incoming links), stop and resolve remaining references; do not delete the file.
4. **Delete retired file**:
   - Once `migration-retirement` passes, delete the legacy standalone DoD file.
5. **Log event and completion (`migration-complete`)**:
   - Record the `workspace.migration` event via `log-append` passing the active `operationPath`.
   - Run `migration-complete` to verify destination preservation, proven file absence, zero remaining references, and updated baselines.
   - Invalidate inventory cache via `invalidate-project-index`.

## Failure recovery

- If interrupted, re-verify existing file hashes against the checkpoint.
- Applied effects are skipped; do not duplicate log events on retry.
- Any unexpected external edit during migration produces a conflict and suspends the operation safely.
