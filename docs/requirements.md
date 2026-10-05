# Daily Tasks requirements

Accepted through the design conversation, 2026-10-05. Public plugin and repository
`NyssaAI/daily-tasks`, version 0.1.0. This document records the product decisions;
implementation progress belongs in commits and verification receipts.

## Product boundaries

R1. Skills supply bounded capabilities, not an autonomous agent persona. Personal
user perspective, across projects and delegated work. The caller coordinates.
No calendar scheduling, duration fitting, deadlines, review-on dates or paused state.
Priority suggestions explain their basis; the user selects work. Existing selected
unfinished items carry forward automatically. Changing priorities needs user acceptance.

R2. Explicit acceptance (including batch acceptance) is required to create projects,
milestones and tasks through the skill. Manual new checklist rows are candidates,
not accepted tasks. Suggestions, requests, promises and silence do not count as acceptance.

R3. Exactly one authoritative definition per record. Project index and daily plan
are editable Markdown views. Reconcile user edits into authoritative records before
refreshing views. Conflicts block only affected items; never last-write-wins.

R4. Every tracked item including project, milestone, task, DoD criterion, blocker
and plan has a UUIDv7 hidden in Markdown comments. Wiki links carry human labels
and adjacent hidden `ref` IDs. Renames/moves preserve identity; maintain backlinks.
Missing/duplicate IDs affect only involved records; never guess or silently re-ID.

R5. Each milestone folder directly contains task files and `definition-of-done.md`.
The project has `project-index.md`, milestone folders and a sibling `blockers/`.
DoD is milestone-level only. Visible checklists indent tasks under milestones;
blockers form a separate list at the bottom. No displayed UUIDs. HTML is deferred.

R6. PARA and file-management are optional changeable conventions, not imports or
runtime dependencies. `document-maturity` is independent of project-state,
milestone-state, task-state and blocker-state. Tags are optional classifications.
The related agent-skills change renames legacy maturity `status` explicitly.

R7. Human `owner` is an email; default is the configured user. Only a user can
designate/change owner. Optional `assignee` is a human email or stable agent name;
people and agents may assign/reassign. When absent owner performs the work.
Assignment is independent of lifecycle; sessions do not define agent identity.

R8. Projects/milestones/tasks: not-started, in-progress, completed, cancelled.
Blockers: open, resolved. Created/updated timestamps, optional started/resolved
timestamps and optional target_date use ISO 8601 GMT (Z). target_date never inherits
or is calculated. Explicit activity required for start, including retrospective
reports. Keep event/activity time and recorded time. Unclear activity time defaults
to now; retain original wording and fallback indication in the log. Display all
times in configured local IANA timezone with timezone label. Dates in daily-plan
filenames represent the user's local day.

R9. Dependencies are informational task-to-task completion relationships, separate
from usually external blockers. No start prohibition or override ceremony. Cancelled
prerequisites remain linked and visibly flagged, never treated as fulfilled.
Shared blockers have one record, resolution condition and reciprocal references;
resolve only when the condition is met, not when one affected project closes.

R10. Milestone closure requires satisfied DoD, no open preventing blockers, and all
tasks completed, moved or cancelled. Project closure requires all milestones completed
or cancelled and no preventing blockers. Checkboxes request validation, never silently
complete children. Parent cancellation requires explicit child dispositions, batch allowed.
Task cancellation is strikethrough plus Cancelled, not a completion checkbox.

R11. Reopened tasks automatically reopen completed parent milestone/project; manually
unchecking a task restores in-progress with recorded start, else not-started. Reopening
blockers/DoD reopens completed affected parents but leaves completed tasks unchanged.
Task moves across projects preserve IDs/state/history/relationships/ownership, refresh
links and reopen completed destinations for unresolved tasks. Closed parents are not
automatically reclosed. Reopening cancelled work requires an explicit disposition.

R12. Check-in is anytime, resumable, scoped to configured local day. Create only today's
missing plan; never backfill skipped days. Carry from most recent earlier plan,
including delegated work. Completed/cancelled items stay visible that day, don't carry.
Removing a selected task keeps its task open and stops carry-forward until selected again.
Repair unambiguous interrupted operations without duplicate log entries; preserve
ambiguous changes as pending conflicts and continue independent work. Missing files
retain references; deletion never means cancelled/completed.

R13. Explicit setup captures current user's name/email, IANA timezone, priorities,
vault root and projects root. Configuration and reconciliation/check-in state reside
under explicitly chosen `.nyssaai/daily-tasks/`. No cwd/cache-derived scope.
This is configuration and operating state only. Daily Markdown plans use the configured
vault output directory; accepted task documents use the projects directory. Neither is
stored under configRoot. Existing state locations require explicit migration approval.
Daily plans: `{vault-root}/2-areas/daily-plans/yyyy.mm.dd-daily-plan.md`, configurable
for alternate conventions. Log: `{projects-root}/.daily-tasks/yyyy.mm.dd-decisions.json`;
prefix is file creation date, not daily rollover. One plugin-wide logical history,
segmented archives permissible. Independent projects roots represent independent installs.

R14. JSON log accessed exclusively through JS for validation, append/query/archive and
performance. Append-only corrections reference originals; preserve archived IDs/content.
Consequential decisions only (acceptance, assignments, lifecycle, moves, target/priority
changes, blockers, conflict resolution, selection/removal). No read/no-op noise.
Compact history supports decision reconstruction; it is not a full document backup.

R15. Narrow executable scope: IDs, timestamps, metadata/link validation, change detection,
closure checks and scoped repair/recovery proposals. Skills author Markdown. No central
task engine, no auto-scheduling or autonomous acceptance. Keep minimal reconciliation
baselines separate from history. Stable operation IDs enable retry deduplication.

## Delivery and verification

U1 shared contract + portable plugin; U2 log interface; U3 integrity/reconciliation;
U4 router, setup, capture, records, day planning and check-in skills; U5 PARA migration;
U6 generated adapters, static checks, integration tests, independent review/evaluation.
Public-source examples must be synthetic. Native host activation requires independent
evidence; static package checks and direct CLI execution cannot establish it.
