# Daily Tasks requirements

Accepted through the design conversation, 2026-10-05. Public plugin and repository
`NyssaAI/daily-tasks`, version 0.2.0. This document records the product decisions;
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

R4. Every tracked document including project, milestone, task, DoD, blocker
and plan has a UUIDv7 in scalar frontmatter `id`. Legacy hidden own IDs remain
readable and must agree with frontmatter if both occur. DoD criterion IDs remain
hidden Markdown comments. Wiki links carry human labels
and adjacent hidden `ref` IDs. Renames/moves preserve identity; maintain backlinks.
Missing/duplicate IDs affect only involved records; never guess or silently re-ID.

R5. Each `m{number}-{milestone-name}/` folder directly contains a matching milestone
Markdown file, `t{number}-{task-name}.md` files, and flat `inputs/` and `outputs/`
holding folders. The milestone file explains the milestone and owns milestone DoD.
Each task file owns its requirements and task DoD. The project has `project-index.md`
and a sibling `blockers/` containing `b{number}-{name}.md` records. Blocker
numbers are project-local, stable and never reused; legacy unnumbered blockers remain
readable until an explicitly requested rename. Navigation follows project -> milestone -> task -> files;
no task subfolders or indexes within the holding folders. Keep local project work
inside the project; scratch uses its `.temp/`. Link shared inputs and consumed outputs
at their existing home. Preserve sources and resolve file collisions without loss.
Number milestones within projects and tasks within milestones; labels do not change
on reorder and UUIDs remain the identity. Names are lowercase descriptive kebab-case.
Use the next number above existing/retired labels, never reuse retired numbers.
The required depth overrides optional PARA flattening advice. Editable project tables
may retain task summaries; blockers form a separate table. No displayed UUIDs.
New tasks/milestones use record_version: 2. Legacy names and separate DoD files stay
readable until authorized migration, which preserves identities, criteria and history.
Missing legacy task criteria require accepted facts, never inference from completed state.

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

R10. New task completion requires satisfied task DoD and no open preventing blockers.
Milestone closure requires satisfied milestone DoD, no open preventing blockers, and all
tasks completed, moved or cancelled. Project closure requires all milestones completed
or cancelled and no preventing blockers. Checkboxes request validation, never silently
complete children. Parent cancellation requires explicit child dispositions, batch allowed.
Task cancellation uses `[-]` with strikethrough plus Cancelled; `[x]` means completed.

R11. Reopened tasks automatically reopen completed parent milestone/project; manually
unchecking a task restores in-progress with recorded start, else not-started. Reopening
blockers/milestone DoD reopens completed affected parents but leaves completed tasks
unchanged. Unchecking task DoD reopens that task and its completed parents.
Task moves across projects preserve IDs/state/history/relationships/ownership, refresh
links and reopen completed destinations for unresolved tasks. Closed parents are not
automatically reclosed. Reopening cancelled work requires an explicit disposition.

R12. Check-in is anytime, resumable, scoped to configured local day. Create only today's
missing plan; never backfill skipped days. Carry from most recent earlier plan,
including delegated work. Completed/cancelled items stay visible that day, don't carry.
Removing a selected task keeps its task open and stops carry-forward until selected again.
Rollover runs once per local day regardless of whether future selection pre-created
today's plan. Merge prior unfinished selections by UUID, preserve existing rows and
explicit removals/future allocations, and persist dated completion only after
verified effects. Interrupted rollover remains recoverable, not falsely complete.
Repair unambiguous interrupted operations without duplicate log entries; preserve
ambiguous changes as pending conflicts and continue independent work. Missing files
retain references; deletion never means cancelled/completed.

R13. Setup resolves the current user's name/email, timezone, optional priorities,
vault root and projects root. Use `timezone: "system"` to resolve the host zone
on each run, or an explicit IANA override. New profiles
default to system detection, report the detected zone, and preserve the sentinel
in configuration. Existing explicit zones remain overrides. First-use setup asks
only preference scope and missing name/email routinely; timezone questions are
reserved for detection failure and priorities are optional.
Preferences use vault-local or user-level `.nyssaai/daily-tasks/`; reconciliation
and check-in state use the vault's independent stateRoot or established state location.
Reuse applicable configuration pointers, common state roots and known vault scope before
asking questions. Resolve absolute paths from context; do not require the user to type
them or separately approve state initialization. The host may capture its initial
vault-root working directory once as an explicit binding. Later subprocess cwd,
plugin cache paths and daily-plan directories must never determine resolved roots.
On first use without existing configuration or an explicitly chosen scope, ask:
"Configure Daily Tasks for this vault only, or for all vaults you access?"
The answer selects vault-local or user-level preferences using conventional locations;
do not ask for internal storage paths or repeat the scope question on routine use.
Personal preference reuse must preserve independent vault output and operating state.
Each planning session binds exactly one vault, its assigned projects root and its
daily-plan root. Shared user preferences do not permit cross-vault planning or ID
lookup. External projects storage is allowed only through the root explicitly
assigned to that vault. Bind inventory results, numbered screens and recovery
checkpoints to this context; reject another binding and use a separate session.
This is configuration and operating state only. Daily Markdown plans use the configured
vault output directory; accepted task documents use the projects directory. Neither is
stored under configRoot. Existing state locations require explicit migration approval.
Daily plans: `{vault-root}/2-areas/daily-plans/yyyy.mm.dd-daily-plan.md`, configurable
for alternate conventions.

Users may independently configure Markdown formatting templates or completed examples
for project indexes, daily plans, milestones, tasks and the interactive review screen.
Persist optional absolute or portable `./...` and `~/...`
Markdown paths in `templates.projectIndex`, `templates.dailyPlan`,
`templates.milestone`, `templates.task` and `templates.planDayReview` in the existing profile. Examples
control visible presentation while preserving metadata, IDs, editable projections,
relationships and accepted facts. Missing configured templates require replacement or
explicit reset; omitted preferences use bundled defaults. Registration does not
authorize reformatting existing documents or accepting sample work.
Log: `{projects-root}/.daily-tasks/yyyy.mm.dd-decisions.json`;
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

R16. A separate deterministic project-inventory operation builds a derived JSON
summary of projects, milestones, open tasks and relevant blockers from canonical
Markdown. Store it at `<vaultRoot>/.temp/daily-tasks/project-index.json`, not in
configuration or retained records. It is disposable, rebuildable cache; deleting it
must not lose accepted work, selections, pending operations or reconciliation state.
Task paths are relative to projectsRoot, never persisted host-specific absolute paths.
Collection also reads authoritative persisted future-day selections and joins them
to task UUIDs. Open-task summaries expose `planned` entries, each containing `date`
and `source`, with no separate duplicate dates array;
future-allocated tasks stay in inventory/open counts but are excluded from today's
addition options. Planned dates are YYYY.MM.DD calendar dates without a time or
offset; timezone changes do not shift them. The effective timezone determines
today for date comparisons. Source daily-plan paths are relative to vaultRoot.
Dated daily-plan files are the sole durable selection authority. An explicit future
selection creates that date's plan if absent, using the configured template. Each
task has only one active planning date; `planned` contains zero or one current/future
entry. Historical daily plans remain intact and do not count as active dates.
Moving work transfers the active selection between dates under the recovery protocol.
Conflicting active dates require clarification, not silent selection of one date.
List-row IDs may be inline or on the immediately following comment-only reference
line. Matching references identify one task; conflicting references remain invalid,
not new capture candidates. Blank lines, other comments, headings and fences break
association. Legacy unchecked strikethrough `Cancelled` rows express cancelled state
with an unchecked checkbox, including future allocations; reconcile them against
baselines. `[x]` continues to mean completed regardless of a stale cancellation caption.
Future target_date values alone never imply allocation. Missing/ambiguous allocation identities produce diagnostics, not
an assumption that work is available. Known selection changes invalidate affected
cached summaries before TTL expiry. The planning skill owns dated-plan writes and
enforcement of one active date; inventory only collects their committed rows.
Pending screen decisions suppress repeat
options within their review but do not count as persisted allocation evidence.
Use the agreed [inventory JSON shape](features/f-001/inventory.example.json).
Sort projects by directory date, oldest first, breaking ties alphabetically by name;
undated directories follow alphabetically by name. Preserve milestone/task order
from project indexes in arrays, without position fields. Valid unlisted tasks follow
listed tasks by filename for stable display, without implying execution priority or
blocking them. Milestone sequence still requires authoritative index references.
Calculate counts, lateness, future-date eligibility and the lowest
incomplete milestone when consuming the inventory, using current identity and the
effective timezone/local day; do not persist these convenience fields.
Include source fingerprints, schema version, UTC `generatedAt` timestamp and integrity
diagnostics. Discovery never selects work for the day or supplies acceptance.
Configure cache lifetime explicitly as nonnegative integer `projectIndex.ttlSeconds`
in the effective profile, initially defaulting to `14400` (four hours). Zero disables reuse. An explicit refresh request always
rebuilds the index. Otherwise refresh only when the inventory is needed and the cache
is absent, malformed, incompatible, known to have changed sources/scope, or its age
is greater than or equal to the configured TTL. Missing or future timestamps make
the cache unusable. Before reuse perform lightweight source-change checks, including
project directory membership and relevant project/daily-plan file metadata.
Detected edits/additions/deletions/moves invalidate the cache; plugin writes
invalidate affected data immediately. Refresh content hashes during rebuild;
unchanged metadata is not proof of unchanged content. Do not infer fresh data from
the cache file's filesystem mtime or reset generatedAt
when merely reading/copying the cache. Within TTL, the index is a dated snapshot;
canonical record checks and reconciliation remain required for affected changes.
Detect additions/deletions/moves during refresh and write atomically. A failed
refresh must not present stale data as current or advance generatedAt. An explicit
refresh completes only after a successful rebuild. Changed editable views must be surfaced
for reconciliation before their affected task statuses inform planning; indexing
does not resolve conflicts or update canonical Markdown. No background scheduling.
Routine inventory access uses the CLI directly. A broader reconciliation pass may
use one shared maintenance subagent to refresh inventory and propose reconciliation
changes, with separate inventory and reconciliation freshness timestamps. Prefer
`gpt-6-luna` on Codex, Haiku on Claude, or a supported comparable lightweight model.
Select the model explicitly when the host supports it and report unavailable model
selection rather than claiming it happened. The parent skill remains responsible
for authorized Markdown changes and verified persistence. This delegation policy
does not authorize another worker solely for deterministic indexing.

R17. Plan review presents the broader available-work inventory, alongside existing
daily selections, rather than limiting the user to a small recommended shortlist.
Distinguish selected work from candidate additions, personal from delegated work,
and blocked work from actionable work. Preserve stable display order and carry-forward
rules; discovery never selects work implicitly. Do not rank today's tasks, ask for
execution-order decisions or add an ordering screen. Execution order belongs to
the person. After selection, recap the plan and proceed to save and verify. The user
review follows a process defined by screen templates. Screen sequence, fields,
navigation and decision handling remain to be specified with the user. These
interaction templates are distinct from the saved daily-plan document template;
no graphical UI or screen implementation is implied by this requirement.
The first local-day check-in includes an ownership-focused task-addition review
screen beginning with user-owned open project, open task and late task counts.
Show tasks owned by the user regardless of assignee, without delegated categories,
assignee details, blockers, blocker counts or a Needs clarification section.
Delegation remains the owner's subsequent choice; reconciliation conflicts remain
in their separate workflow. Selections outside this view are preserved in the plan.
Existing selections are
preserved; the broader eligible inventory is offered for explicit additions, with
no requirement to add work. First-check-in status comes from successful check-in
state, not plan-file existence. Late means an open task's explicit target_date is
earlier than today's configured local date; due today is not late. Inventory counts
deduplicate records and disclose incomplete or uncertain source data. The draft
screen is `docs/templates/plan-day-select-tasks-screen.md` and awaits user revision.
Planning/review task screens share the legend `[ ] not started · [>] in progress ·
[x] completed · [-] cancelled` and accept
stable row-number responses using symbols or natural-language actions. Keep screen
selection distinct from work status. Preserve owner when delegating via assignee.
Interpret clear batch items independently, retain unresolved questions and do not
infer acceptance from silence. Shared skill rules live in
`skills/daily-tasks/references/response-conventions.md`. Delegation is a separate
action represented by assignee, not a lifecycle symbol. Blocker rows use `[ ] open ·
[x] completed (resolved)`; completion replies persist resolved, with no separate
completed blocker state or implicit completion of affected work. No mandatory future-day allocation
or automatic scheduling is inherited from Personal CoS.
Daily selection screens and recaps display today only; tomorrow and other future-day
tables require an explicit week-view request. Preserve original item numbering and
the screen's table layout in recaps. Mark unresolved selections carried from the
most recent earlier plan with ↺ in the task cell and explain it in the legend;
carry-forward provenance is distinct from canonical state and day selection.
Selection-screen and recap columns are #, Status, Project, Milestone, Task and Due Date.
Status symbols reflect canonical progress; selected/available sections indicate
day membership. `[x]` never means selected. Adding work does not mark it started
or completed, and carried-forward work retains its actual canonical status.
This screen also accepts explicit task-status updates, including collective reports
such as "2, 4, 6 are in progress". Update canonical task records and applicable
parent effects/project views before projecting their state into the daily plan,
under the recovery/log protocol. Status updates do not implicitly select work.
Clarify ambiguous commands before their affected writes. Addition options follow
project directory date/name order and task order within each project, using only the first
incomplete milestone in its authoritative sequence unless all milestones are
explicitly requested. Skip completed/cancelled milestones; retain already selected
later-milestone work. Unknown milestone ordering must be resolved, not replaced with
priority or UUID sorting. Limit each page to 15 addition options, exposing remaining
eligible work via Show more without renumbering existing items. Counts remain full
inventory totals. Exclude explicit future-day selections from addition options on
all pages and recaps; a future target date alone is not a future selection.

## Delivery and verification

U1 shared contract + portable plugin; U2 log interface; U3 integrity/reconciliation;
U4 router, setup, capture, records, day planning and check-in skills; U5 PARA migration;
U6 generated adapters, static checks, integration tests, independent review/evaluation.
Public-source examples must be synthetic. Native host activation requires independent
evidence; static package checks and direct CLI execution cannot establish it.
