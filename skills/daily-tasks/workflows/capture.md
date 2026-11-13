> [!IMPORTANT] Scope Directive
> This workflow owns extracting candidate commitments from authorized sources, deduplicating against existing vault records, and obtaining explicit individual or batch user acceptance before record creation. It does NOT own vault/profile setup (`setup.md`), canonical Markdown record creation or repair (`records.md`), daily plan task selection (`plan.md`), or non-actionable PARA reference/knowledge note filing (route to `para-vault` in `agent-skills`).

# Capture and accept

Extract candidate tasks, milestones, and projects from user notes or configured sources without creating unaccepted records. Reference [record conventions](../references/records.md) for entity identity rules.

## 1. Scope and source scan gates

1. **Enforce all four full-setup gates**:
   - Verify live `daily_tasks_*` MCP tools in the current harness, `~/.nyssa-ai/daily-tasks/config.json` (`"schema_version": 2`, `projectsRoot`, `dailyPlansRelative`, `sources`, `user.email`, IANA `timezone`), and vault templates baseline (`~/.nyssa-ai/daily-tasks/templates/updates.json`).
   - If **any** gate is incomplete, **immediately halt** capture and complete [Setup](setup.md) first.
   - Read only user-supplied inputs and explicitly authorized `sources` (`directories`, `mcps`, `harnessConnections`).
2. **Check the daily auto-scan gate** *(when `sources.autoScan: true` or on explicit `"scan my sources"` / `"check inbox"` commands)*:
   - Inspect `<runtime_root>/source-scans/YYYY.MM.DD.json` for today's local date.
   - If the receipt is absent (or an explicit scan was requested), scan configured `sources.directories` (relative paths without traversal) and connected read-only MCP sources, write `<runtime_root>/source-scans/YYYY.MM.DD.json`, and collect candidate items.
   - If today's scan receipt already exists and no explicit scan was requested, skip automatic rescanning.
3. **Route daily plan selection requests**:
   - If the user is selecting existing accepted tasks for today's plan rather than extracting new work, route immediately to [Daily plan](plan.md).

## 2. Candidate extraction and deduplication

1. **Classify and deduplicate**:
   - Distinguish actionable requests, commitments, ideas, and status updates on existing work; non-actionable reference/knowledge notes and source-record filing belong to `para-vault` (`agent-skills`) rather than candidate tasks.
   - Match extracted items against existing record UUIDs and source references in `projectsRoot` before proposing a new candidate.
   - Treat repeated mentions of an existing task as context or a status update on that record, never as a duplicate task.
   - Keep `in-progress` tasks in ongoing selections rather than the candidate acceptance queue.
2. **Present the candidate queue**:
   - Render a compact candidate list showing:
     - Proposed `title` and `record_kind` (`project`, `milestone`, or `task`)
     - Target parent `project` / `milestone`
     - `owner` (defaulting to current user email; never guess other owners) and `assignee` (if explicitly stated; omitted means `owner`)
     - `target_date` (only when explicitly stated in the source; never infer or fabricate dates)
     - Source citation and any unresolved questions
   - Persist unfinished candidates and their stable source keys in `<runtime_root>/candidates.json`.

## 3. Explicit acceptance gate and handoff

1. **Enforce affirmative user acceptance**:
   - Require an explicit individual or batch acceptance reply from the user (e.g., `"Accept all? [Y]"`).
   - Treat a direct user command naming specific work to create (e.g., `"create M1: update LinkedIn and resume in this project"`) as explicit acceptance for that named item only; ask only for material missing facts and do not auto-accept extra agent-suggested tasks.
   - **Never** treat silence, default proposal selections, promises quoted in source text, agent approvals, or manually typed unlinked checkboxes as acceptance.
   - Record declined or deferred candidate dispositions in `<runtime_root>/candidates.json` so subsequent check-ins do not re-propose unchanged items.
2. **Ensure parent hierarchy exists**:
   - Every accepted task requires an accepted parent milestone and project.
   - If a parent project or milestone does not exist yet, offer to accept and create the parent project/milestone together with the task rather than silently fabricating a catch-all project.
3. **Hand off accepted items to Records**:
   - Route accepted items to [Records](records.md) to allocate UUIDv7 IDs, write canonical Markdown files, update parent indexes, and append the decision log entry in `<runtime_root>/decision-log.json`.

## Verification

Before reporting capture completion:
- [ ] Confirm every created project, milestone, or task had explicit user acceptance (or a direct named creation command).
- [ ] Confirm unaccepted, declined, or unanswered items remain in `<runtime_root>/candidates.json` and were not written as canonical Markdown records under `projectsRoot`.
- [ ] Confirm any handoff to [Records](records.md) persisted the canonical Markdown files and decision-log entries on disk, and report clickable links along with the remaining unresolved candidate count.
