> [!IMPORTANT] Scope Directive
> This workflow owns creating, updating, moving, delegating, closing, reopening, and surgically repairing canonical Markdown project, milestone, task, and blocker records. It does NOT own candidate extraction (`capture.md`), daily plan selection (`plan.md`), anytime check-in orchestration (`checkin.md`), or canonical schema specifications (owned by `../references/records.md`).

# Manage records

Execute canonical record mutations and surgical Markdown repairs under the domain contracts in [records](../references/records.md), [operation protocol](../references/operations.md), and [MCP / CLI interface](../references/cli.md).

## 1. Pre-flight and acceptance gates

1. **Ensure workspace setup is complete**:
   - If project setup is not already done, trigger and complete [Setup](setup.md) first to establish `workspaceRoot`, `projectsRoot`, and `dailyPlansRelative`.
   - Reuse established profile settings and `<workspaceRoot>/.nyssa-ai/daily-tasks/` operating state without prompting for separate setup approval.
2. **Verify identity and acceptance**:
   - Resolve existing projects, milestones, tasks, and blockers by their frontmatter UUIDv7 `id`.
   - Require explicit user acceptance via [Capture](capture.md) (or a direct user command naming the work to create) before creating any new project, milestone, or task.

## 2. Record creation and metadata checklist

1. **Apply active formatting templates**:
   - Prepare the matching `projectIndex`, `milestone`, or `task` template layout per [custom templates](../references/templates.md) and [template updates](../references/template-updates.md).
   - Use the bundled blocker layout for external blockers under `blockers/b{number}-{name}.md`.
   - Keep Definition of Done (`## Definition of Done`) embedded inside each milestone or task file with `<!-- id: UUIDv7 -->` comments; **never** create standalone DoD files.
2. **Enforce frontmatter and ownership rules**:
   - Set `record_version: 2`, a unique UUIDv7 `id`, `type` (`project` | `milestone` | `task` | `blocker`), `title`, `created_at` (UTC ISO-8601 ending in `Z`), `updated_at` (UTC ISO-8601), and lifecycle state (`project-state`, `milestone-state`, `task-state`, or `blocker-state`).
   - Set `owner` to a human email address (defaulting to the current user); **never** alter `owner` without an explicit human instruction.
   - Set optional `assignee` when delegated (human email or agent name; omitted means `owner` performs the work).
   - Set `target_date` (`YYYY-MM-DD`) only when explicitly provided by the user.
3. **Place files in canonical hierarchy**:
   - Create milestones at `<projectsRoot>/<project>/m{number}-{name}/m{number}-{name}.md` with sibling task files `t{number}-{name}.md` and flat `inputs/` and `outputs/` directories (never subdivide holding folders).
   - Create external blockers at `<projectsRoot>/<project>/blockers/b{number}-{name}.md` and link `## Blocked by` / `## Blocks` reciprocally.
   - Link task dependencies reciprocally under `## Depends on` / `## Required by` (dependencies inform order and never block starting work).
   - Update parent milestone and `project-index.md` navigation tables with `[[relative-path|Title]] <!-- ref: UUIDv7 -->`.

## 3. Lifecycle transitions, moves, and closure

1. **Record lifecycle transitions**:
   - Update `task-state` / `milestone-state` / `project-state` (`not-started`, `in-progress`, `completed`, `cancelled`) or `blocker-state` (`open`, `resolved`) using UTC ISO-8601 timestamps (`started_at`, `resolved_at`, `updated_at`), preserving prior timestamps in append-only history.
   - Keep cancelled records visible in parent and daily views with strike-through and `[-]` status markers.
2. **Enforce closure and reopening gates**:
   - **Before marking completed**: Verify all embedded `## Definition of Done` checkboxes are `[x]`, all child tasks/milestones are terminal (`completed` or `cancelled`), and no open preventing blockers exist. Never silently check DoD items or complete children.
   - **Before cancelling a parent**: Collect explicit user dispositions (batch cancel or move) for all active child records.
   - **When reopening work**: If a task or DoD criterion is unchecked, or a preventing blocker is reopened, clear `resolved_at` and reopen any completed parent milestone and project in the same operation.
3. **Execute safe moves and renames**:
   - Check destination paths for filename collisions before moving.
   - Preserve the record's UUIDv7 `id`, lifecycle timestamps, `owner`, `assignee`, dependencies, and blocker links.
   - Update parent lineage IDs (`project_id`, `milestone_id`) and reciprocal backlinks, verify the new file on disk, and remove the old file only after verification so duplicate live IDs never coexist.
   - If an unfinished task is moved into a completed milestone or project, reopen the destination parent hierarchy.

## 4. Surgical repair of malformed files

When a work record (`project-index.md`, milestone, task, or blocker) is reported as malformed (e.g., in `payload.malformed_files` from `daily_tasks_start_session` or `daily_tasks_get_session_state`, during check-in, or directly by the user):
1. Read the malformed Markdown file directly at the reported path and inspect the diagnostic code (e.g., `unclosed-frontmatter`, `invalid-record`, missing `id`, non-canonical state such as `state: done`, or missing `# <title>`).
2. Surgically repair the YAML frontmatter and required structural headings according to [records and views](../references/records.md):
   - Assign a new UUIDv7 `id` if the frontmatter `id` is missing.
   - Normalize the state key and value (`task-state`, `milestone-state`, `project-state`, or `blocker-state`).
   - Ensure required scalar keys (`id`, `type`, `title`, `owner`, state, `record_version: 2`) and the top-level `# <title>` heading are present.
   - Repair reciprocal project/milestone wiki-links and `<!-- ref: UUID -->` / `<!-- id: UUID -->` comments.
3. Preserve all user prose, body notes, checkboxes, and extra lines byte-for-byte.
4. Re-validate the repaired file and report the exact surgical fixes applied.

## 5. Transactional persistence

1. Apply standalone record edits in order per [operation protocol](../references/operations.md):
   - Write checkpoint -> update canonical task/milestone/project records -> update `project-index.md` views -> update affected daily-plan views -> append decision log and refresh baselines.
2. Invalidate the cached project index (`<workspaceRoot>/.temp/daily-tasks/project-index.json`) immediately after any committed batch modifies canonical records or views.
3. If any step or decision-log write fails, retain the recovery checkpoint and report what changed on disk without claiming completion.

## Verification

Before reporting completion of any record management or repair task:
- [ ] Confirm all modified or created Markdown files contain valid flat scalar YAML frontmatter (`record_version: 2`, UUIDv7 `id`, `type`, `title`, `owner`, UTC timestamps, and canonical state key).
- [ ] Confirm parent milestone and `project-index.md` views contain matching `[[relative-path|Title]] <!-- ref: UUID -->` links and no duplicate UUIDs exist.
- [ ] Confirm surgical repairs preserved all user notes and body text intact.
- [ ] Confirm the decision log and baseline state were updated (or staged via the active MCP session) and provide clickable file links to all changed records.
