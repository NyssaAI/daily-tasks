---
name: daily-tasks-records
description: Create explicitly requested or accepted projects, milestones and tasks; update progress, ownership, assignment, DoD, dependencies and external blockers; fix or repair malformed record files; move, cancel or reopen records consistently. Use when asked to create named work, mark done, reassign, fix malformed files, or change an existing record. A direct named create instruction supplies acceptance without another acceptance prompt.
---

# Manage records

Read [records](../daily-tasks/references/records.md), [operation protocol](../daily-tasks/references/operations.md)
and the needed [CLI operation](../daily-tasks/references/cli.md). If project setup is not already done,
trigger and run [setup](../daily-tasks-setup/SKILL.md) first to establish workspace and project bindings.
Resolve profile and scope through setup; reuse established settings and
conventional state paths without a separate setup approval. Continue the record request
once required values are available.

1. Identify existing work by UUID. New projects/milestones/tasks require recorded explicit
   user acceptance via [capture](../daily-tasks-capture/SKILL.md), not implied approval.
2. Use templates and `new-id` for new records and DoD criteria. All projects/milestones/tasks/
   blockers have human email owner (default current user) and optional assignee. The user
   chooses owner; agent may execute that direction but never change it autonomously.
   Either person/agent can change assignee. No assignee means owner is doing the work.
   Prepare only the matching `projectIndex`, `milestone` or `task` kinds through
   [template updates](../daily-tasks/references/template-updates.md). Retain the baseline,
   offer relevant revisions and use `active.content`, following
   [custom templates](../daily-tasks/references/templates.md). Postponement leaves the
   active layout usable; adoption alone never reformats existing records.
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
   prepare any explicitly requested task state before calling `reopen-ancestors`; apply
   required parent changes in the same pending operation under the records contract.
8. Move/rename only after checking destination collision and identity. Preserve task UUID,
   lifecycle, owner/assignee, dependencies and blocker refs; update parent IDs and backlinks.
   Verify new location and links before removing old file; don't leave two live IDs.
   Unresolved work reopens completed destination parents, including across projects.
9. Fix malformed files: When a work record (project index, milestone, task, blocker) is malformed
   (e.g., reported in `payload.malformed_files` by `daily_tasks_start_session` or `daily_tasks_get_session_state`,
   detected during check-in, or identified directly by the user):
   - Read the malformed file directly at the reported path.
   - Inspect the error code and message (e.g. `unclosed-frontmatter`, `invalid-record`, missing UUID, non-canonical state like `state: done` instead of `task-state: completed` / `not-started`, missing title).
   - Surgically repair the document according to [records and views](../daily-tasks/references/records.md) and domain specifications (`docs/specs/`).
   - Preserve all user notes, body comments, checkboxes, and extra lines byte-for-byte.
   - If the frontmatter is missing a UUID `id`, assign a new UUIDv7.
   - Standardize the state field (`task-state` for tasks, `milestone-state` for milestones).
   - Ensure the required frontmatter keys (`id`, `type`, `title`, `owner`, `task-state`/`milestone-state`, `record_version: 2`) and H1 `# <title>` are present.
   - Retain and repair reciprocal project/milestone wiki-links and hidden `<!-- ref: UUID -->` comments.
   - Validate the repaired record and report the surgical fixes applied.
10. Apply via operation protocol: checkpoint, Markdown changes, validation, log, refresh views,
    baselines. Return exact changed links and remaining conflicts. Keep cancelled rows visible
    with strike-through. Missing or duplicated files are conflicts, not new task creation.
    For task status replies, verify canonical tasks, required parent effects and project
    views before updating daily-plan views. A failed earlier effect retains the checkpoint.

After a committed batch changes canonical records or project/daily-plan projections,
call `invalidate-project-index` with the resolved workspaceRoot immediately, including
when a later effect fails. The next planning request rebuilds before using that cache.
Rebuild now only when the current workflow needs inventory; no background refresh.

Expose proposed changes when unable to write/execute. Do not claim a complete operation
if the log failed; retain recovery checkpoint and explain what already changed.
