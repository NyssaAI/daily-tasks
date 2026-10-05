# Records, identity and views

## Scope and paths

Setup selects absolute configRoot (the `.nyssa/daily-tasks` directory), vaultRoot,
and projectsRoot. Keep all settings and reconciliation/check-in state outside the
installed plugin. Default daily plans: `vaultRoot/2-areas/daily-plans/YYYY.MM.DD-daily-plan.md`.
The prefix is the user's local day, not UTC. Configuration may override that convention.
Log is projectsRoot/.daily-tasks/YYYY.MM.DD-decisions.json, named at creation, with
rotation suffixes as needed. One logical history, archives included by the log CLI.
Never read or edit those JSON logs directly from a skill.

Project content belongs below the chosen projectsRoot. For a PARA vault follow its
accepted project naming conventions, with this flat layout:

```text
project/
  project-index.md
  milestone-name/
    milestone.md
    definition-of-done.md
    task-name.md
  blockers/
    approval-needed.md
```

`project-index.md` owns project metadata and renders subordinate records. `milestone.md`
owns milestone metadata. Individual task/blocker files own their facts. DoD file owns
the milestone criteria. Daily/project checklists are editable views, not other copies
of those task definitions. Do not silently rename existing files to match defaults.
The explicit project-index.md product convention takes precedence over PARA's dated
index default. PARA is optional; never import its installed paths or require its loader.

## Metadata and Markdown contract

Use the [task](../assets/task.md), [milestone](../assets/milestone.md),
[DoD](../assets/definition-of-done.md), [blocker](../assets/blocker.md),
[project](../assets/project-index.md) and [daily plan](../assets/daily-plan.md) templates.
Replace placeholders before writing. Generate IDs with CLI `new-id`, never fabricate them.
Each tracked record/criterion has one `<!-- id: UUIDv7 -->`. Projections and links use
`<!-- ref: UUIDv7 -->`. UUIDs must not appear in the readable body. Raw source comments
are necessarily visible to a source editor. Preserve IDs through rename, reorder, move.

Frontmatter uses one scalar per line: strings, JSON-quoted strings, booleans or null.
Only `tags` may use a JSON array of strings. No nested YAML, anchors, multiline
scalars or other YAML arrays in managed metadata v1.
Keep arbitrary rich text below frontmatter. Relations live in body sections, not lists
inside YAML. Unsupported metadata is reported, never discarded or silently rewritten.

Required: `type`, `title`, `owner` (email), `created_at`, `updated_at`, plus the named
state field for project/milestone/task/blocker. Optional `assignee`, `started_at`,
`resolved_at`, `target_date`, `document-maturity`. Parent IDs `project_id`, `milestone_id`
are metadata, hidden in rendered frontmatter. DoD uses type `dod`, parent IDs and criteria.
When PARA conventions apply, retain its `created` date and `document-maturity` as
separate note metadata; never interpret legacy `status` as execution state.

Projects/milestones/tasks: `not-started`, `in-progress`, `completed`, `cancelled`.
Blockers: `open`, `resolved`. No paused state, deadline or review_on. Task display:
`[x]` completed; `[ ]` not-started/in-progress; `[ ] ~~Title~~ — Cancelled` cancelled.
Unchecking completed task -> in-progress if started_at exists, otherwise not-started.
Distinguish source row removal (deselect daily work) from file deletion (missing record).

## References

```markdown
## Depends on
- [[other-task|Other task]] <!-- ref: UUIDv7 -->

## Blocked by
- [[../blockers/approval-needed|Approval needed]] <!-- ref: UUIDv7 -->
```

Dependency counterparts use `## Required by`; blocker counterpart `## Blocks`.
Use paths relative to the containing document, slash separators, optional `.md`,
and readable aliases. UUID reference is the identity; path is navigation. Never repair
identity from a similar title. Duplicate IDs or missing targets stay unresolved and
do not prevent independent work. `check-links` identifies mismatches before repairs.
Dependencies are visible context only. Cancelled prerequisite stays linked and flagged
"prerequisite cancelled"; it does not satisfy a prerequisite or prohibit starting work.

## Closure and reopening

Milestone closes only with every DoD criterion satisfied, all children explicitly
completed/moved/cancelled, and no open preventing blocker. Project closes only when
all milestones are completed/cancelled and no open preventing blocker. Use `check-closure`.
DoD satisfaction is a supplied decision with evidence where available, not an inference
from completed tasks. A checked parent with unmet conditions is a closure request;
leave it open, explain reasons. Parent cancellation likewise requires explicit child
dispositions; offer batch cancellation, never silently cascade cancellation.

Reopening a task reopens completed parents. Unchecking DoD or reopening a preventing
blocker also reopens completed affected parents, while completed tasks stay completed.
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
