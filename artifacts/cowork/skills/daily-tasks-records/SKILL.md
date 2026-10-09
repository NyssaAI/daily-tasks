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
   Use the profile's matching `templates.projectIndex`, `templates.milestone` or
   `templates.task` when supplied, following
   [custom templates](../daily-tasks/references/templates.md). Load only the template
   for the record being authored. An omitted preference uses its bundled template.
   Use the bundled blocker template. DoD belongs only in milestone/task files;
   never create a standalone DoD file or template.
   A provisional task template can be
   trialled when requested without promoting its maturity. Fill its input paths,
   references, required skills, output destination, verification and delivery mode
   from accepted task details; ask only for missing information needed to execute.
3. Keep requirements and task DoD in each task file; milestone explanation and milestone
   DoD belong in the milestone file. New records use `record_version: 2`.
   Create `m{number}-{name}/m{number}-{name}.md` with sibling `t{number}-{name}.md`
   task files and flat `inputs/` and `outputs/` directories. Follow the parent-local
   numbering, file placement and navigation rules in records; never subdivide holding
   folders. Link relevant files from tasks and tasks from milestone/project views.
   Keep the UUID in frontmatter and use the record naming/move rules for existing files.
   A delegation packet links assigned task (including its requirements, DoD, input/output
   paths), milestone and relevant dependencies/blockers;
   do not clone task authority or tie assignee to an ephemeral session. Delegation isn't start.
4. Create blockers in their owning project as `blockers/b{number}-{name}.md`,
   using project-local numbers and the same stable-number rules as milestones/tasks.
   External blocker records state impediment and what resolves it, with optional evidence.
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
   For task status replies, verify canonical tasks, required parent effects and project
   views before updating daily-plan views. A failed earlier effect retains the checkpoint.

For an authorized conversion of existing work, follow
[workspace migration](../daily-tasks/references/workspace-migration.md). An ordinary
record update does not authorize bulk migration or inventing task criteria.

After a committed batch changes canonical records or project/daily-plan projections,
call `invalidate-project-index` with the resolved vaultRoot immediately, including
when a later effect fails. The next planning request rebuilds before using that cache.
Rebuild now only when the current workflow needs inventory; no background refresh.

Expose proposed changes when unable to write/execute. Do not claim a complete operation
if the log failed; retain recovery checkpoint and explain what already changed.
