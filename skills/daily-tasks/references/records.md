# Records, identity and views

> [!IMPORTANT] Scope Directive
> This reference owns the canonical Markdown schemas, UUIDv7 identity model, directory layout, reciprocal link conventions, and closure/reopening domain rules for project, milestone, task, and blocker records. It does NOT own step-by-step record creation or repair execution checklists (owned by [`../workflows/records.md`](../workflows/records.md)), MCP/CLI invocation syntax (owned by [`cli.md`](cli.md)), transactional checkpoint mechanics (owned by [`operations.md`](operations.md)), daily planning flows (owned by [`planning-flow.md`](planning-flow.md)), or interactive screen formatting (owned by [`response-conventions.md`](response-conventions.md)).

## Workspace structure and paths

Daily Tasks operates on a bound workspace context with four distinct logical roots: `workspaceRoot` (the base directory for the active workspace), `projectsRoot` (the root directory containing all project folders, which may reside in external storage bound to the workspace), `dailyPlansRoot` (the destination for dated `<dailyPlansRoot>/YYYY.MM.DD-daily-plan.md` files), and `stateRoot` (the workspace-isolated operational state directory at `<workspaceRoot>/.nyssa-ai/daily-tasks`). Every record or planning session binds to a single workspace context and never mixes inventories or resolves UUIDs across separate workspaces.

### Project directory layout

Project content resides under `projectsRoot` using a two-level hierarchy of project folders, milestone folders (`m{N}-{name}/`), and project-scoped blocker folders (`blockers/`):

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

`project-index.md` owns the project-level metadata and milestone navigation table. Each milestone directory contains a milestone definition file (`m{N}-{name}.md`) owning the milestone explanation, milestone Definition of Done (DoD), and child task links, alongside sibling task files (`t{N}-{name}.md`). Each task file is the single authoritative record for that task's requirements, embedded DoD criteria, input links, and output links. Flat `inputs/` and `outputs/` directories sit beside task files for attachments and deliverables; they never contain nested subdirectories or task definitions and are excluded from record discovery. External blockers reside under `blockers/b{N}-{name}.md` within their single owning project, though they may link reciprocally to affected records in other projects.

### File and record numbering

Record filenames use lowercase kebab-case (`m{N}-{name}.md`, `t{N}-{name}.md`, `b{N}-{name}.md`) with sequential positive integers allocated locally: milestones within a project, tasks within a milestone, and blockers within a project. Retired or cancelled numbers are never reused, files are never renumbered for visual sorting, and numbers carry no priority meaning. Because authoritative identity is governed by the frontmatter UUIDv7 `id` rather than the filename, editing a record's title does not require renaming its file, and moving a record preserves its number unless a collision exists at the destination.

## Document and metadata contract

### Frontmatter schema

Every tracked Markdown record begins with flat scalar YAML frontmatter containing a unique UUIDv7 `id`. Nested YAML objects, YAML anchors, and multiline scalars are prohibited; only single scalar key-value pairs (strings, numbers, booleans, `null`) and `tags` (formatted as a single-line JSON array of strings) are permitted.

For `project`, `milestone`, and `task` records (`record_version: 2`), required keys are `id` (UUIDv7), `type` (`project` | `milestone` | `task`), `title` (string), `owner` (human email address), `created_at` (UTC ISO-8601 ending in `Z`), `updated_at` (UTC ISO-8601), and the type-specific lifecycle state key (`project-state`, `milestone-state`, or `task-state` with values `not-started` | `in-progress` | `completed` | `cancelled`). Optional keys include `assignee` (human email or agent name, defaulting to `owner` when omitted), `started_at` (UTC ISO-8601), `resolved_at` (UTC ISO-8601), `target_date` (`YYYY-MM-DD`), `tags`, and parent lineage IDs (`project_id`, `milestone_id`). For `blocker` records, required keys are `id` (UUIDv7), `type: blocker`, `title`, `owner`, `created_at`, `updated_at`, and `blocker-state` (`open` | `resolved`).

### Definition of Done (DoD)

Tasks and milestones each contain exactly one embedded `## Definition of Done` section; standalone DoD files are prohibited. Each DoD criterion is a Markdown checkbox (`- [ ]` or `- [x]`) paired with a unique UUIDv7 HTML comment (`<!-- id: UUIDv7 -->`) on the same line or the immediately following comment line. Embedded DoD criteria use `id:` comments, whereas task and milestone projections inside views use `ref:` comments.

### Projection formatting and inter-record references

Checklists and tables inside `project-index.md`, milestone overviews, and daily plans are read/write views over canonical records rather than independent task definitions. View rows link to canonical files using human-readable aliases and hidden UUID reference comments (`[[relative-path|Task title]] <!-- ref: UUIDv7 -->`, with the pipe escaped as `\|` inside Markdown table cells). Task status symbols are `[ ]` (`not-started`), `[>]` (`in-progress`), `[x]` (`completed`), and `[-]` (`cancelled`); blocker status symbols are `[ ]` (`open`) and `[x]` (`resolved`).

Inter-record relationships live in dedicated body sections using reciprocal links: task dependencies use `## Depends on` and `## Required by` (which inform sequencing without prohibiting execution start), while impediments use `## Blocked by` and `## Blocks`. Ordinary contextual wiki-links to reference notes or attachments omit the `<!-- ref: UUIDv7 -->` comment.

## Closure and reopening lifecycle

### Closure invariants

A record can transition to `completed` only when its completion conditions are verifiably satisfied on disk:
- **Task closure**: All checkboxes in the task's non-empty `## Definition of Done` section are checked (`[x]`) and no open preventing blockers exist in `## Blocked by`.
- **Milestone closure**: All milestone `## Definition of Done` criteria are checked, every child task is in a terminal state (`completed` or `cancelled`), and no open preventing blockers remain.
- **Project closure**: Every milestone in the project is in a terminal state (`completed` or `cancelled`) and no open preventing blockers remain.

Completion of child tasks or DoD criteria is never inferred silently. Cancelling a parent milestone or project requires explicit dispositions (cancellation or move) for its active children and never cascades silently.

### Reopening propagation

When work under a completed parent becomes active again, reopening propagates upward to maintain hierarchy consistency while preserving unaffected sibling records:
- **Task reopened**: Unchecking a task or one of its DoD criteria reopens the task (transitioning to `in-progress` if `started_at` is present, or `not-started` otherwise, unless the user specifies an explicit state), clears `resolved_at`, and automatically reopens any completed parent milestone and project.
- **Milestone DoD unchecked or blocker reopened**: Unchecking a milestone DoD criterion or reopening a preventing blocker reopens the affected completed milestone and project and clears their `resolved_at` timestamps, while leaving already-completed child tasks untouched.

## Time and actor conventions

All stored and logged timestamps use UTC ISO-8601 format ending in `Z` (such as `2026-11-04T14:30:00Z`), while user-facing text renders times in the user's configured local timezone. `target_date` represents an explicit user deadline or target and is never inferred, inherited from parents, or calculated automatically. Moving, delegating, or selecting a task for a daily plan never transitions it to `in-progress`; starting execution requires an explicit start report.

Every record has a human `owner` (email address) and an optional `assignee` (human email or agent identifier). Only an explicit human instruction can set or change `owner`; agents may update `assignee` when delegating work, and an omitted `assignee` means the `owner` performs the task.
