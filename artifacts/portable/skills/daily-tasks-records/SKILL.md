---
name: daily-tasks-records
description: Create accepted projects, milestones and tasks; update progress, ownership, assignment, DoD, dependencies and external blockers; move, cancel or reopen records consistently.
---

# Manage records

Read [records](../daily-tasks/references/records.md), [operation protocol](../daily-tasks/references/operations.md)
and the needed [CLI operation](../daily-tasks/references/cli.md). Resolve profile and
scope through [setup](../daily-tasks-setup/SKILL.md); reuse established settings and
conventional state paths without a separate setup approval. Continue the record request
once required values are available.

1. Identify existing work by UUID. New projects/milestones/tasks require recorded explicit
   user acceptance via [capture](../daily-tasks-capture/SKILL.md), not implied approval.
2. Use templates and `new-id` for new records and DoD criteria. All projects/milestones/tasks/
   blockers have human email owner (default current user) and optional assignee. The user
   chooses owner; agent may execute that direction but never change it autonomously.
   Either person/agent can change assignee. No assignee means owner is doing the work.
3. Keep task instructions, context and desired output in its file. DoD is only milestone-level.
   A delegation packet links assigned task, milestone DoD and relevant dependencies/blockers;
   do not clone task authority or tie assignee to an ephemeral session. Delegation isn't start.
4. External blocker records state impediment and what resolves it, with optional evidence.
   Link `Blocks` / `Blocked by` reciprocally. Shared blocker remains independent of each
   project's lifecycle. Completing "request approval" does not resolve "approval pending".
5. Task dependencies use `Depends on` / `Required by`. They never prohibit starting work
   or require an override. Flag cancelled prerequisites without removing their relationships.
6. Record explicit starts/completions/cancellations/resolutions, including retrospective ones.
   `activity-time` supplies event and record time; retain original wording/fallback in log.
   Validate chronology without fabricating precision. Update current lifecycle timestamp,
   preserving old values in append-only history. targets are optional explicit input only.
7. For closure use `check-closure`; never silently complete children or infer DoD evidence.
   For cancelling parents collect explicit child dispositions (batch allowed). For reopening,
   use `reopen-ancestors` and apply required parent changes in the same pending operation.
8. Move/rename only after checking destination collision and identity. Preserve task UUID,
   lifecycle, owner/assignee, dependencies and blocker refs; update parent IDs and backlinks.
   Verify new location and links before removing old file; don't leave two live IDs.
   Unresolved work reopens completed destination parents, including across projects.
9. Apply via operation protocol: checkpoint, Markdown changes, validation, log, refresh views,
   baselines. Return exact changed links and remaining conflicts. Keep cancelled rows visible
   with strike-through. Missing or duplicated files are conflicts, not new task creation.

Expose proposed changes when unable to write/execute. Do not claim a complete operation
if the log failed; retain recovery checkpoint and explain what already changed.
