> [!IMPORTANT] Scope Directive
> This workflow owns extracting candidate commitments from authorized sources, deduplicating against existing workspace records, and obtaining explicit individual or batch user acceptance before record creation. It does NOT own workspace/profile setup (`setup.md`), canonical Markdown record creation or repair (`records.md`), or daily plan task selection (`plan.md`).

# Capture and accept

Extract candidate tasks, milestones, and projects from user notes or configured sources without creating unaccepted records. Reference [record conventions](../references/records.md) for entity identity rules.

## 1. Scope and source scan gates

1. **Verify workspace setup**:
   - Resolve the active profile and workspace roots through [Setup](setup.md) if project setup is not already complete.
   - Read only user-supplied inputs and explicitly authorized `sources` (`directories`, `mcps`, `harnessConnections`).
2. **Check the daily auto-scan gate** *(when `sources.autoScan: true` or on explicit `"scan my sources"` / `"check inbox"` commands)*:
   - Inspect `<stateRoot>/source-scans/YYYY.MM.DD.json` for today's local date.
   - If the receipt is absent (or an explicit scan was requested), scan configured workspace `sources.directories` (relative paths without traversal) and connected read-only MCP sources, write `<stateRoot>/source-scans/YYYY.MM.DD.json`, and collect candidate items.
   - If today's scan receipt already exists and no explicit scan was requested, skip automatic rescanning.
3. **Route daily plan selection requests**:
   - If the user is selecting existing accepted tasks for today's plan rather than extracting new work, route immediately to [Daily plan](plan.md).

## 2. Candidate extraction and deduplication

1. **Classify and deduplicate**:
   - Distinguish actionable requests, commitments, ideas, and status updates on existing work.
   - Match extracted items against existing record UUIDs and source references in `projectsRoot` before proposing a new candidate.
   - Treat repeated mentions of an existing task as context or a status update on that record, never as a duplicate task.
   - Keep `in-progress` tasks in ongoing selections rather than the candidate acceptance queue.
2. **Present the candidate queue**:
   - Render a compact candidate list showing:
     - Proposed `title` and record `type` (`project`, `milestone`, or `task`)
     - Target parent `project` / `milestone`
     - `owner` (defaulting to current user email; never guess other owners) and `assignee` (if explicitly stated; omitted means `owner`)
     - `target_date` (only when explicitly stated in the source; never infer or fabricate dates)
     - Source citation and any unresolved questions
   - Persist unfinished candidates and their stable source keys in `<stateRoot>/candidates.json`.

## 3. Explicit acceptance gate and handoff

1. **Enforce affirmative user acceptance**:
   - Require an explicit individual or batch acceptance reply from the user (e.g., `"Accept all? [Y]"`).
   - Treat a direct user command naming specific work to create (e.g., `"create M1: update LinkedIn and resume in this project"`) as explicit acceptance for that named item only; ask only for material missing facts and do not auto-accept extra agent-suggested tasks.
   - **Never** treat silence, default proposal selections, promises quoted in source text, agent approvals, or manually typed unlinked checkboxes as acceptance.
   - Record declined or deferred candidate dispositions in `<stateRoot>/candidates.json` so subsequent check-ins do not re-propose unchanged items.
2. **Ensure parent hierarchy exists**:
   - Every accepted task requires an accepted parent milestone and project.
   - If a parent project or milestone does not exist yet, offer to accept and create the parent project/milestone together with the task rather than silently fabricating a catch-all project.
3. **Hand off accepted items to Records**:
   - Route accepted items to [Records](records.md) to allocate UUIDv7 IDs, write canonical Markdown files, update parent indexes, and append the decision log entry with source and actor provenance.

## Verification

Before reporting capture completion:
- [ ] Confirm every created project, milestone, or task had explicit user acceptance (or a direct named creation command).
- [ ] Confirm unaccepted, declined, or unanswered items remain in `<stateRoot>/candidates.json` and were not written as canonical Markdown records under `projectsRoot`.
- [ ] Confirm any handoff to [Records](records.md) persisted the canonical Markdown files and decision-log entries on disk, and report clickable links along with the remaining unresolved candidate count.
