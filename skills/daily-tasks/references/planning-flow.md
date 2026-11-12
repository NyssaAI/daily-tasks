# Context, inventory and planning

> [!IMPORTANT] Scope Directive
> This reference owns the domain architecture, lifecycle invariants, review eligibility rules, once-per-day carry-forward model, and future-day selection semantics for Daily Tasks planning sessions. It does NOT own step-by-step workflow execution checklists (owned by [`../workflows/plan.md`](../workflows/plan.md) and [`../workflows/checkin.md`](../workflows/checkin.md)), MCP/CLI invocation syntax (owned by [`cli.md`](cli.md)), transactional checkpoint mechanics (owned by [`operations.md`](operations.md)), record schemas (owned by [`records.md`](records.md)), or interactive screen legends and reply parsing (owned by [`response-conventions.md`](response-conventions.md)).

Daily Tasks planning operates within a single bound vault context (`vault_root`) and its associated projects, daily plans, and `runtime_root` operational state.

```text
Daily Tasks Planning Architecture
│
├── 1. Vault & Runtime Binding (## Resolve once)
│   ├── Single bound vault (vault_root, projectsRoot, dailyPlansRoot)
│   ├── Host clock & local IANA day resolution
│   └── Mutable operating state in runtime_root (zero .nyssa-ai/ in vault_root)
│
├── 2. Inventory & Maintenance Boundaries (## Load and maintain)
│   ├── Cached project-index in .temp/ with freshness sidecar
│   └── Scoped diagnostic isolation (malformed files or broken links never freeze unrelated work)
│
├── 3. Communication Collection (## Message collection)
│   ├── Per-source fetch window (saved cursor or 7-day default initial lookback)
│   └── Shared cursor filtering across CommunicationClient connectors and host connections
│
├── 4. Daily Carry-Forward (## Once-per-day rollover)
│   ├── In-progress persistence and unfinished selection carry (↺)
│   └── Explicit deselection tracking (removedIds)
│
├── 5. Interactive Review Scope (## Build and review & ## Review scope)
│   ├── All-owner visibility across incomplete milestones (M1, M2, ...)
│   └── Project-paginated numbered screens validated against planDayReview
│
└── 6. Persisted Plan & Future Allocations (## Saved daily plan & ## Future-selection transaction)
    ├── Role separation (My work, Delegated work, Follow-up work)
    └── Single active planning date per task across dated plans
```

## Resolve once

A planning session binds exactly one `vault_root`, one `projectsRoot` (default `1-projects`), one `dailyPlansRoot` (default `2-areas/daily-plans`), and one `runtime_root` for the duration of the session. Inventories, numbered screen handles, and record mutations are never mixed across vaults. Operational state—including `fetch-cursors.json`, `suggestions.json`, `decision-log.json`, `sessions/`, checkpoints, rollover receipts, and review mappings—lives in `runtime_root` (`--runtime-root` -> `NYSSA_RUNTIME_ROOT` -> agent persona `cwd` with `SOUL.md`+`IDENTITY.md` -> `~/.nyssa-ai/daily-tasks/runtime/`), never inside `<vault_root>/.nyssa-ai/`.

When resolving the planning date for today, the host clock and configured IANA timezone determine the local calendar day, even when the current UTC date differs. Requesting a plan for a specific target date scopes the plan selection to that date without overriding the system clock used for audit timestamps. Context bindings (`planningBinding`, `contextBinding`, `inventoryBinding`, and `mappingBinding`) act as opaque hashes over the normalized roots and inventory state so any intervening write or root mismatch invalidates stale session state before side effects can occur.

## Load and maintain

Vault inventory discovery indexes valid project, milestone, task, and blocker records under `projectsRoot`. When a cached index exists at `<vault_root>/.temp/daily-tasks/project-index.json` with a valid freshness sidecar, readers can reuse the parsed graph without re-reading unchanged task files; any committed record or plan write immediately invalidates that sidecar. Relative paths remain anchored to their logical roots, with external project collections outside the vault anchored as `@projectsRoot`.

Diagnostic issues discovered during vault reading—such as a malformed Markdown record (`payload.malformed_files`) or a broken navigation link—are treated as scoped diagnostics rather than a global freeze. Only the affected record is suspended or routed for non-destructive repair via [`../workflows/records.md`](../workflows/records.md), while independent rollover, message matching, and daily planning continue normally. Maintenance inspections are strictly read-only and never fabricate worker evidence or mutate canonical Markdown records.

## Message collection

Stage 0 of a planning session gathers unread email and chat messages from enabled communication sources using a single shared cursor per source stored in `<runtime_root>/fetch-cursors.json`. Both standalone read-only `CommunicationClient` implementations (`CommunicationClientGmail`, `CommunicationClientSlack`) and host-supplied assistant connections (`sources.harnessConnections`) share the same fetch-window and deduplication semantics.

`daily_tasks_get_fetch_window` computes each source's `since` timestamp (ISO-8601 UTC), `after_epoch` (Unix seconds), `last_external_id`, and `has_cursor` flag. When a saved cursor exists, it governs the window start; on a first pull without a cursor, the window reaches back `initial_lookback_days` (7 days by default, configured via `sources.initialLookbackDays` or `--initial-lookback-days`). All host message reads are strictly read-only and never send, reply to, draft, label, archive, or mark messages read.

Incoming messages at or before `since`, prior to the first-pull cutoff, or matching `last_external_id` are filtered out, and duplicate `(source, external_id)` pairs are collapsed. Remaining messages are correlated against the vault `StateGraph` to produce numbered Screen 1 update suggestions citing their source. Each checked source's cursor advances in memory only and is persisted to disk exclusively when `daily_tasks_confirm_plan(confirmed=true)` succeeds; cancelling a session leaves stored cursors untouched so unread messages are re-evaluated on the next run. If a communication source fails to connect, it is reported to the user and omitted from `checked_sources` without blocking the planning session.

## Build and review

The interactive review flow presents numbered screens generated and validated by the MCP planning session (`daily_tasks_start_session`, `daily_tasks_execute_operations`, and `daily_tasks_advance_screen`) or verified against the active `planDayReview` template. Rollover and pre-matched message suggestions appear on Screen 1, per-project task assignment on Screen 2 (paginated one project per page), and the confirmation recap on Screen 3.

The session maintains a stable 1-based row-number-to-UUID mapping across screen refreshes and pagination so the user can reference any displayed suggestion or task by its row handle. Resuming an active session restores the current screen and project pagination state, and the rendered `payload.screen` markdown is displayed unchanged so the user always sees the validated table structure, status indicators, carry markers, and legends.

## Review scope

Review visibility spans all valid tasks in the bound `projectsRoot` regardless of owner or assignee, allowing the user to plan personal tasks, oversee delegated work, and track third-party follow-up items from a unified inventory. Viewing a task in a planning screen never alters its assignment, transfers ownership, or starts execution.

Inventory summary counts distinguish four categories:
- **Open tasks**: Tasks in `not-started` state without a future-day allocation or current-day selection.
- **In-progress tasks**: Tasks currently undergoing execution, tracked with ongoing selections rather than new options.
- **Open projects**: Unfinished projects containing at least one open task.
- **Late tasks**: Open tasks whose explicit `target_date` falls strictly before the configured local day (`due today` is not late).

Projects are ordered by directory date (oldest first) with alphabetical tie-breaking, followed by undated project directories alphabetically. Within each project, tasks from incomplete milestones (`not-started` or `in-progress`) are presented in authoritative milestone sequence (`M1`, `M2`, `M3`, …) while completed and cancelled milestones are skipped. Within a milestone, tasks follow canonical index order and then filename order; this sequence provides stable display handles and never implies priority ranking or execution order. Only unselected `not-started` tasks without a future-day allocation appear as available options to add.

## Saved daily plan

When the user confirms the plan (`daily_tasks_confirm_plan(confirmed=true)`), the persisted `<dailyPlansRoot>/YYYY.MM.DD-daily-plan.md` document separates selected tasks into three role sections based on ownership and effective assignment:
- **My work**: Tasks where the effective assignee (the explicit `assignee`, or `owner` when unassigned) matches the current user's email, including work owned by others.
- **Delegated work**: Tasks owned by the current user where the effective assignee is another person or an agent.
- **Follow-up work**: Tasks where both `owner` and effective `assignee` are third parties.

The saved document follows the active `dailyPlan` template layout, including `# Daily plan — LOCAL_DATE`, summary counts (`Open projects: ... Open tasks: ... Late tasks: ...`), `**Timezone:**`, `**Updated:**`, `## Selected for today` with `### My work`, `### Delegated work`, and `### Follow-up work`, `#### PROJECT_TITLE / MILESTONE_TITLE` group subheadings, 6-column tables (`| # | Status | Project | Milestone | Task | Due Date |`), `Legend:`, `## Blockers`, `## Decisions`, and `## Notes and references`.

Task cells render human-readable wiki-links with escaped pipes and hidden UUID reference comments (`[[relative-path\|Task title]] <!-- ref: UUID -->`), prefixed by `↺ ` outside the link when carried forward. Raw filesystem paths and bare UUIDs are never exposed as display labels. Status cells reflect canonical task lifecycle indicators (`[ ]`, `[>]`, `[x]`, `[-]`). Completed and cancelled tasks remain visible on the day they reach a terminal state, while unselected available options stay out of the saved plan. Daily plans never include automatic time-slot scheduling, duration estimates, or capacity fitting.

## Once-per-day rollover

Carry-forward from the nearest preceding daily plan into today's plan runs deterministically once per local calendar day. If today's plan already exists on disk, rollover preserves its frontmatter `id`, original `created_at` timestamp, existing selections, and user prose.

Carry-forward obeys three core domain invariants:
- **In-progress persistence**: Every valid `in-progress` task in the vault inventory is carried into today's plan—even if it was absent from yesterday's plan or previously deselected—until it is explicitly completed, cancelled, or moved to a future date.
- **Unfinished selection carry**: Unfinished `not-started` tasks selected on the nearest prior plan carry forward into today's plan with carry provenance (`carriedFrom`) and the `↺` marker, unless the user explicitly deselects (`unplan`) them for today (recorded in `removedIds`).
- **Terminal and future exclusion**: Completed (`[x]`), cancelled (`[-]`), and future-allocated tasks do not carry forward into subsequent days, while unresolved or missing task references are preserved visibly to prevent silent data loss.

## Future-selection transaction

Assigning a `not-started` task to an explicit future date (`assign-to-day` with a future `YYYY-MM-DD`) ensures that each task has at most one active planning date across the vault. Moving a task from today's plan to a future date writes or updates the target future daily plan and records the deselection in today's state (`removedIds`) so the task is removed from today's active selections and excluded from today's available-options list until that future date arrives or the task is explicitly re-selected.
