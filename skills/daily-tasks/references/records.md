# Records, identity and views

## Scope and paths

Setup resolves absolute configRoot from an existing settings pointer, an established
`.nyssaai` common state root, or the known vault convention, in that order. It reuses
known vaultRoot and projectsRoot rather than asking for them again; see
[setup discovery](../../daily-tasks-setup/SKILL.md#resolve-configuration-and-scope).
configRoot holds `profile.json` and optional copied templates. stateRoot holds
reconciliation baselines, pending operations, candidates and check-in progress.
`resolve-context` defaults stateRoot to the selected vault's `.nyssaai/daily-tasks`;
reuse an established explicit legacy stateRoot. Keep these outside the
installed plugin. Daily plans and accepted task documents are user output and must stay
outside configRoot, including legacy `.nyssa/daily-tasks` state directories.
Daily plans resolve from the profile's `vaultRoot` and `dailyPlansRelative`, never from
the profile file's parent directory. Resolve missing output settings through setup's
accepted conventions and defaults; clarify only unresolved scope or invalid destinations.
Never fall back into configuration storage. Default daily plans:
`vaultRoot/2-areas/daily-plans/YYYY.MM.DD-daily-plan.md`.
The prefix is the user's local day, not UTC. Configuration may override that convention.
Log is projectsRoot/.daily-tasks/YYYY.MM.DD-decisions.json, named at creation, with
rotation suffixes as needed. One logical history, archives included by the log CLI.
Never read or edit those JSON logs directly from a skill.

Project content belongs below the chosen projectsRoot. For a PARA vault follow its
accepted project naming conventions, with this required milestone workspace layout.
Its depth takes precedence over PARA suggestions to flatten projects:

```text
project/
  project-index.md
  m1-milestone-name/
    m1-milestone-name.md
    t1-task-name.md
    t2-task-name.md
    inputs/
    outputs/
  blockers/
    b1-approval-needed.md
```

Every planning/records request uses one vault's fixed resolved context. Its configured
projectsRoot can be external storage explicitly assigned to that vault. Do not look
up missing IDs in other vaults, combine project roots, or apply numbered replies to
another vault. Preserve unresolved cross-vault pointers for clarification and use
a separate planning session for other vault work. Shared home preferences do not
make records, plans, checkpoints or screen mappings shared.

`project-index.md` owns project metadata and links milestones. Each milestone file
owns its explanation, milestone DoD and task navigation. Each task file owns its
requirements, task DoD, input links and output links. Daily/project/milestone task
checklists are editable views, not copies of task definitions. Individual blocker
files own their facts. Do not silently rename existing files to match defaults.
New managed filenames use lowercase letters, lowercase `.md`, and descriptive
kebab-case words: `m1-launch-readiness.md`, `t1-prepare-budget.md`, `b1-approval-needed.md`. Match the milestone
folder and file stems. Allocate milestone numbers within a project and task numbers
within a milestone. Allocate blocker numbers within their owning project, storing new
blockers as `blockers/b{number}-{name}.md`. A shared blocker has one owning project
and may link work in other projects; do not copy it or allocate a new number per link.
Legacy unnumbered blockers remain readable; rename only when explicitly requested.
Use the next unused positive integer above existing and recorded
retired numbers; check files and history through `log-query`, never read log JSON.
Never reuse a cancelled/deleted record's number, renumber for sorting, or treat numbers
as schedule/priority. A move keeps its number unless it collides in the destination;
then allocate a destination-local number and log the old/new mapping. Keep its stable
UUID in frontmatter; a title change does not require a filename change. Use a
descriptive qualifier for collisions and avoid Windows reserved device names.
Fixed document names and dated daily-plan filenames keep their established forms.
Legacy uppercase Markdown is still discovered and receives `noncanonical-filename`
advice with a proposed name. It remains usable; rename only through the move protocol,
checking collisions and updating links without changing identity or lifecycle.
The explicit project-index.md product convention takes precedence over PARA's dated
index default. PARA is optional; never import its installed paths or require its loader.

### Files and navigation

Create `inputs/` and `outputs/` directly beside the milestone/task files, even when
empty. They are flat holding areas: no task subfolders, shared/ folders, or extra
index files inside them. All local project work stays in the project; disposable
scratch belongs in its `.temp/`. Requirements and DoD stay in task/milestone files.
Put supplied files directly in inputs/, preserving native formats and source details
in the consuming task's Inputs section. Use descriptive filenames; when names collide,
compare identity/content and use a meaningful qualifier for distinct files. Never
overwrite an unrelated file or duplicate a shared working input for each task.
Put deliverables directly in outputs/ and link them from the producing task's Result
and Output sections. When another task consumes that output, link its existing home
from that task's Inputs section. Replacing a deliverable requires explicit task scope;
otherwise preserve the earlier version with a meaningful version qualifier.
External source links retain provenance; imported working copies live in inputs/.
External delivery requires its own authority and a receipt linked in the task.

The navigation chain is project index -> milestone -> task -> relevant files.
Maintain it during ordinary work: add accepted tasks to their milestone and project
views, update task input/output links as files arrive, and repair affected incoming
and outgoing links on moves. Use relative links resolved from the containing note.
File links are ordinary navigation, without managed UUID refs. Before removing a
source after a move, verify target content, task links, milestone/project navigation,
and affected daily-plan links. Preserve historical references with clear provenance.
Holding areas are excluded from managed-record discovery even if an attachment looks
like a task document; they cannot create phantom tasks or duplicate live identities.

## Metadata and Markdown contract

Use the [task](../assets/task.md), [milestone](../assets/milestone.md),
[blocker](../assets/blocker.md),
[project](../assets/project-index.md) and [daily plan](../assets/daily-plan.md) templates.
Definitions of done must be embedded in their milestone or task file only. Never
create a standalone DoD file or template. Existing standalone records are readable
solely for explicit legacy migration; they are not an authoring option.
Replace placeholders before writing. Generate IDs with CLI `new-id`, never fabricate them.
For project indexes, daily plans, milestones and tasks, configured user examples take precedence over
bundled visible formatting; follow [custom templates](templates.md). The metadata,
identity and editable-reference contract below still applies.
Each tracked document has one scalar frontmatter `id: UUIDv7`. Legacy document
`<!-- id: UUIDv7 -->` comments remain readable; if both exist they must agree.
Preserve existing IDs and move their representation only during an authorized
document update/migration. DoD criteria retain `<!-- id: UUIDv7 -->` comments.
Projections and links use
`<!-- ref: UUIDv7 -->`. UUIDs must not appear in the readable body. Raw source comments
are necessarily visible to a source editor. Preserve IDs through rename, reorder, move.

Only managed references require UUIDs: an explicit ref comment, a checkbox projection,
or a link inside a typed relationship section. Ordinary contextual wiki links to notes,
research or attachments are navigation and may share a line without task identities.
Missing or malformed managed IDs remain errors; they never join other missing IDs.

Frontmatter uses one scalar per line: strings, JSON-quoted strings, booleans or null.
Only `tags` may use a JSON array of strings. No nested YAML, anchors, multiline
scalars or other YAML arrays in managed metadata v1.
Keep arbitrary rich text below frontmatter. Relations live in body sections, not lists
inside YAML. Unsupported metadata is reported, never discarded or silently rewritten.
Validation handles invalid structured text uniformly: retain the offending source,
report its path/field and do not invent an accepted value. An invalid task is excluded
from additions; an invalid project/milestone prevents establishing additions for that
project, including later milestones. Preserve existing selections and unresolved
references, continue unrelated projects, and restore eligibility after correction
and refreshed validation. Ordinary free-text prose is not restricted to state values.
Filename advice is separate from invalid record facts and does not block planning
or closure.

Required: `type`, `title`, `owner` (email), `created_at`, `updated_at`, plus the named
state field for project/milestone/task/blocker. Optional `assignee`, `started_at`,
`resolved_at`, `target_date`, `document-maturity`. Parent IDs `project_id`, `milestone_id`
are metadata, hidden in rendered frontmatter. New tasks and milestones use scalar
`record_version: 2` and exactly one `## Definition of Done` section in their own file.
Use list criteria with `[ ]` or `[x]` and a unique `<!-- id: UUIDv7 -->` on the same
or immediately following comment-only line. Subheadings may group criteria; a heading
at the DoD level or above ends the section. Criteria may link evidence files. Criteria
use `id`, task projections use `ref`; do not use table checkboxes for DoD criteria.
Standalone type `dod` and unversioned tasks remain readable for existing work only;
see [workspace migration](workspace-migration.md). Never create a separate DoD file
for a new milestone or infer missing legacy task criteria from its completion state.
When PARA conventions apply, retain its `created` date and `document-maturity` as
separate note metadata; never interpret legacy `status` as execution state.

Projects/milestones/tasks: `not-started`, `in-progress`, `completed`, `cancelled`.
Blockers: `open`, `resolved`. No paused state, deadline or review_on.
For blocker responses/display, completed (`[x]`) means resolved, and open (`[ ]`)
means unresolved. Persist `blocker-state: resolved` for completion; do not introduce
a separate blocker completed state or complete blocked tasks implicitly.

Task display: `[x]` completed, `[ ]` not-started, `[>]` in-progress, `[-]` cancelled.
Legacy unchecked in-progress rows and struck-through cancelled rows remain readable.
List and table cells retain adjacent UUID refs; escape wiki label pipes in tables.
For list rows, a hidden ref may be on the row or on the immediately following
comment-only line. Both locations must agree if supplied together. Blank lines,
headings, ordinary comments and fenced examples break that adjacency. Conflicting
refs are identity errors requiring resolution, not candidates for new task creation;
never pick an ID or create replacement work. Table refs stay in their own linked cell.
The shared association rule applies to project views, plans and inventory allocations.
Legacy unchecked struck-through Cancelled rows parse as state cancelled with checked
false; reconcile them through their baseline before changing canonical work. Explicit
`[x]` still means completed, even when an old cancellation caption has not been refreshed.
The projection parser also accepts a separate Status cell on a task table row.
Unchecking completed task -> in-progress if started_at exists, otherwise not-started.
Distinguish source row removal (deselect daily work) from file deletion (missing record).

## References

```markdown
## Depends on
- [[other-task|Other task]] <!-- ref: UUIDv7 -->

## Blocked by
- [[../blockers/b1-approval-needed|Approval needed]] <!-- ref: UUIDv7 -->
```

Dependency counterparts use `## Required by`; blocker counterpart `## Blocks`.
Use paths relative to the containing document, slash separators, optional `.md`,
and readable aliases. UUID reference is the identity; path is navigation. Never repair
identity from a similar title. Duplicate IDs or missing targets stay unresolved and
do not prevent independent work. `check-links` identifies mismatches before repairs.
Dependencies are visible context only. Cancelled prerequisite stays linked and flagged
"prerequisite cancelled"; it does not satisfy a prerequisite or prohibit starting work.

## Closure and reopening

Task completion requires its own nonempty DoD to be satisfied and no open preventing
blocker. A new task with missing criteria stays incomplete; obtain its accepted criteria.
Milestone closes only with every milestone DoD criterion satisfied, all children explicitly
completed/moved/cancelled, and no open preventing blocker. Project closes only when
all milestones are completed/cancelled and no open preventing blocker. Use `check-closure`.
DoD satisfaction is a supplied decision with evidence where available, not an inference
from completed tasks. A checked parent with unmet conditions is a closure request;
leave it open, explain reasons. Parent cancellation likewise requires explicit child
dispositions; offer batch cancellation, never silently cascade cancellation.

Reopening a task reopens completed parents. Unchecking its task DoD reopens that task
(in-progress if it has started_at, otherwise not-started) and completed parents.
An explicitly requested supported task state, such as "reopen as not-started", takes
precedence over that checkbox fallback. Put the requested state in the proposed
records passed to `reopen-ancestors`; an old started_at does not override the user's
state decision. Verify the saved task state as well as the required parent effects.
Unchecking milestone DoD reopens that milestone and project, leaving completed tasks
alone. Reopening a preventing blocker reopens completed affected parents, while
completed tasks stay completed. Cancelled work requires an explicit reopening decision.
Use `reopen-ancestors` to calculate changes, then the operation protocol to apply.
Do not erase old completion history. Clear current resolved_at on reopening; the old
value remains in history. Reopening cancelled work requires an explicit desired state.
Moving a task preserves IDs and lifecycle facts; updates parents and all references;
unresolved incoming work reopens completed destinations. Moving is not resolution of
the task itself, but resolves its membership in the original milestone.

## Time and people

Store all event and recorded timestamps in GMT ISO strings ending Z. Render every
time with the user's local timezone explicitly named (use CLI `format-time`).
target_date is optional explicit input, never inherited or calculated. Explicit start
report required; assignment/edit isn't a start. Retrospective start/completion/cancel/
blocker resolution retain activity time and recorded time in the log; when unclear
use now and `time_defaulted: true` with original wording. Interpret a precise local
report using configured timezone; ask if a DST fold makes the specific instant ambiguous,
or use the user-authorized current-time fallback rather than inventing an instant.

Owner must be human email, defaults configured user; only human direction can change it.
An agent can execute that person's instruction, never autonomously choose a new owner.
Assignee may be human email or named agent, either actor may change it; absent = owner.
The parser can check syntax, not authenticate a human; caller supplies actual authority.
