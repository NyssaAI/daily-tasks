# Records, identity and views

> [!IMPORTANT]
> **Scope Directive**: This document defines the canonical schemas, identity model, directory structures, reference links, and closure/reopening lifecycle for Daily Tasks project, milestone, task, and blocker records. It is strictly a record domain specification. Low-level CLI commands and signatures belong in [`cli.md`](cli.md), transactional write-ahead checkpointing and reconciliation in [`operations.md`](operations.md), daily planning flows and rollover in [`planning-flow.md`](planning-flow.md), and interactive review formatting and legends in [`response-conventions.md`](response-conventions.md).

## Workspace structure and paths

Daily Tasks operates on a bound workspace context with defined logical roots:
- `workspaceRoot`: Base directory for the active workspace.
- `projectsRoot`: Root containing all project folders (can be external storage bound to the workspace).
- `dailyPlansRoot`: Root for persisted daily plans (e.g. `<dailyPlansRoot>/YYYY.MM.DD-daily-plan.md` using the user's local day).
- `stateRoot`: Workspace-isolated operational state (`.nyssa-ai/daily-tasks`), holding checkpoints, baselines, and review states.

A planning or record session binds exactly one workspace context. Never mix inventories, search other workspaces for IDs, or apply numbered replies across workspaces.

### Project directory layout

Project content resides strictly under `projectsRoot` using the standard layout:

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

- **Index and milestone files**: `project-index.md` owns project metadata and links milestones. Each milestone file owns its description, milestone DoD, and child task navigation.
- **Task files**: Each task file owns its requirements, embedded DoD, inputs, and outputs.
- **Holding areas**: Flat `inputs/` and `outputs/` directories reside beside task files for attachments and deliverables. They contain no nested subfolders or task definitions, and are excluded from record discovery.
- **Blockers**: Stored under `blockers/b{number}-{name}.md` within their owning project. A blocker has exactly one owning project, but may link to work in other projects via reciprocal references.

### File and record numbering
- Filenames use lowercase kebab-case: `m{N}-{name}.md`, `t{N}-{name}.md`, `b{N}-{name}.md`.
- Allocate sequential positive integers using CLI `next-record-number` (scans active records and decision history). Numbers are scoped locally: milestones within a project, tasks within a milestone, blockers within a project.
- Never reuse a retired/cancelled number, renumber files for sorting, or infer priority from numbers.
- Stable identity is governed by frontmatter UUIDv7, not filenames. Title changes do not require filename changes. Moves retain the original number unless colliding at destination.

## Document and metadata contract

### Frontmatter schema
Every tracked Markdown record must have scalar YAML frontmatter with a unique UUIDv7:
- **Task / Milestone / Project**:
  - Required: `id` (UUIDv7), `type` (`task` | `milestone` | `project`), `title` (string), `owner` (human email), `created_at` (GMT ISO ending in `Z`), `updated_at` (GMT ISO), and state (`task-state` / `milestone-state` / `project-state`: `not-started` | `in-progress` | `completed` | `cancelled`).
  - Optional: `assignee` (human email or agent name; defaults to owner if omitted), `started_at` (GMT ISO), `resolved_at` (GMT ISO), `target_date` (`YYYY-MM-DD`), `tags` (JSON array of strings).
  - Tasks and milestones use scalar `record_version: 2` and hide parent IDs (`project_id`, `milestone_id`) in frontmatter metadata.
- **Blocker**:
  - Required: `id` (UUIDv7), `type: blocker`, `title`, `owner`, `created_at`, `updated_at`, `blocker-state` (`open` | `resolved`).

Frontmatter allows only single scalar key-value pairs (strings, booleans, null) and `tags` as a JSON array of strings. Nested YAML, anchors, and multiline scalars are prohibited.

### Definition of Done (DoD)
- Tasks and milestones must have exactly one embedded `## Definition of Done` section. Standalone DoD files are obsolete.
- DoD items are markdown checkboxes (`- [ ]` or `- [x]`) followed by a unique UUIDv7 comment (`<!-- id: UUIDv7 -->`) on the same line or immediately following comment line.
- Criteria use `id`; task projections in views use `ref`.

### Projection formatting and references
- Checklists and tables in daily plans or project indexes are views, not task definitions.
- Projections link to records using readable aliases and UUID comments:
  `[[relative-path|Task title]] <!-- ref: UUIDv7 -->`
- Task state indicators: `[ ]` not-started, `[>]` in-progress, `[x]` completed, `[-]` cancelled.
- Blocker state indicators: `[ ]` open, `[x]` resolved.
- Inter-record relations live in body sections:
  - Dependencies: `## Depends on` / `## Required by`
  - Blockers: `## Blocked by` / `## Blocks`
- Contextual wiki links to notes or attachments do not use UUID `ref` tags.

## Closure and reopening lifecycle

### Closure rules
Evaluated via CLI `check-closure`:
- **Task**: Satisfies its own non-empty DoD (all criteria checked) and has no open preventing blockers.
- **Milestone**: All milestone DoD criteria satisfied, all child tasks terminal (`completed` or `cancelled`), and no open preventing blockers.
- **Project**: All milestones terminal (`completed` or `cancelled`) and no open preventing blockers.
- Parent cancellation requires explicit child dispositions (batch cancellation or move); cancellation never silently cascades.

### Reopening protocol
Evaluated via CLI `reopen-ancestors` and applied via the operations protocol:
- **Task reopened**: Automatically reopens completed parent milestone and project.
  - If reopening via DoD uncheck: sets task to `in-progress` if `started_at` exists, otherwise `not-started`.
  - Explicit user-requested state takes precedence over defaults.
- **Milestone DoD unchecked**: Reopens milestone and project without modifying completed child tasks.
- **Preventing blocker reopened**: Reopens completed affected parent milestones and projects; child tasks remain completed.
- Reopening clears `resolved_at` on the active record (historical completion preserved in log).

## Time and actor conventions

- **Timestamps**: All stored and recorded event timestamps use GMT ISO format ending in `Z` (e.g. `2026-10-15T13:49:39Z`). User display renders timestamps in the user's explicit local timezone.
- **Target dates**: `target_date` is strictly an explicit user input; never infer, inherit, or calculate it.
- **Execution start**: Moving or assigning a task does not mark it `in-progress`; execution requires an explicit start report.
- **Actors**:
  - `owner`: Must be a valid human email. Only explicit human instruction can change an owner; agents never alter ownership autonomously.
  - `assignee`: Human email or named agent. Either human or agent can change assignment. Defaults to `owner` when absent.
