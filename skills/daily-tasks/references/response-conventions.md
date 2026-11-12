# Planning-screen response conventions

> [!IMPORTANT] Scope Directive
> This reference owns the user-facing presentation model, status and action legends, numbered-handle semantics, and reply interpretation grammar for Daily Tasks planning and check-in screens. It does NOT own step-by-step planning or check-in execution checklists (owned by [`../workflows/plan.md`](../workflows/plan.md) and [`../workflows/checkin.md`](../workflows/checkin.md)), MCP/CLI invocation syntax (owned by [`cli.md`](cli.md)), transactional checkpointing (owned by [`operations.md`](operations.md)), record schemas (owned by [`records.md`](records.md)), or planning domain rules and review scope (owned by [`planning-flow.md`](planning-flow.md)).

## Validated screen presentation model

Interactive daily planning and review screens rely on a strict visual contract so the user can scan work across projects and respond with compact row numbers. Rather than summarizing options in freeform prose or substituting ad-hoc lists, the agent renders the validated `payload.screen` markdown returned by the MCP planning session (`daily_tasks_start_session`, `daily_tasks_execute_operations`, `daily_tasks_advance_screen`, `daily_tasks_get_session_state`) or verified against the active `planDayReview` template unchanged outside code fences. Each actionable row displays a human-readable wiki-link and hidden UUID reference comment (`[[relative-path|Task title]] <!-- ref: UUID -->`) while concealing raw filesystem paths and bare UUIDs from the user's reading flow.

## Presentation legends and meanings

Every review screen concludes with the standard prompt and status legend so the user knows how to format replies and interpret status markers:

```text
Reply by row number and symbol or description:

Legend: [ ] not started · [>] in progress · [x] completed · [-] cancelled
```

When carried-forward work appears on the screen, `· ↺ carried forward` is appended to the legend and carried task titles are prefixed with `↺`. For blocker tables, the legend reads `Legend: [ ] open · [x] completed (resolved)`. Status indicators always reflect the canonical lifecycle state of the underlying task or blocker record rather than whether the item is selected for today's plan; adding a `not-started` task to today's plan preserves its `[ ]` state.

### Status mapping table

| Reply / Symbol | Daily Tasks Meaning | Action Taken |
| :--- | :--- | :--- |
| `[ ]` / `not started` / `pending` | Not started | Retain or reset status via the canonical records protocol. |
| `[>]` / `in progress` | In progress | Record execution start with the current UTC activity timestamp. |
| `[x]` / `complete` / `resolved` | Completed (or Blocker resolved) | Verify DoD criteria and record completion; retain row visibility in today's plan. |
| `[-]` / `cancel` | Cancelled | Cancel the identified record; never cascade silently to parent milestones or projects. |

## Numbered-reply semantics

Actionable table rows on a planning screen are numbered in a single continuous 1-based sequence (`#`), while section headings and summary counters remain unnumbered. Row numbers serve strictly as transient session handles bound to the active vault (`mappingBinding`); they carry no priority ranking, are never reused or renumbered as pages advance, and are never applied across different vaults.

Users may reply using status symbols (with or without brackets), row lists, or natural-language directives such as `1 accept`, `1 x, 2 >, 3 cancel`, `add 2, 4`, or `2 delegate to Alex`. Because a bare row number without an action or verdict is ambiguous, the agent asks for the user's intended action on that row while retaining unambiguous decisions from the same batch. Collective status reports (for example, `2, 4, 6 in progress`) apply to each identified record in memory and commit to canonical records, parent milestones/projects, and daily plan views upon plan confirmation.

## Planning actions grammar

| User Reply Action | Domain Semantics |
| :--- | :--- |
| **add / today** | Assigns an eligible `not-started` task to today's plan (`assign-to-day`) without altering its lifecycle state, `target_date`, or `assignee`. |
| **remove / unplan** | For `not-started` work, deselects the task from today's plan and suppresses automatic carry-forward (`removedIds`) without requiring a new date. For `in-progress` work, prompts for an explicit future date, completion, or cancellation because active work cannot silently drop from plans. |
| **keep** | Retains current selections and statuses; omitted rows remain untouched. |
| **show details** | Displays the full requirements, embedded DoD criteria, and blocker/dependency context for the identified row. |
| **next / show more** | Advances Screen 2 to the next project page of eligible tasks (`Page X of Y`), preserving stable row numbers and prior selections. |
| **previous** | Returns to the preceding project page when `page > 0`. |
| **show all milestones** | Displays tasks from later milestones for inspection while keeping selection eligibility scoped to incomplete milestones in sequence. |
| **later / defer [date]** | Deselects `not-started` work from today and, when an explicit future `YYYY-MM-DD` date is given, assigns the task to that future daily plan (`assign-to-day`) without mutating its `target_date` deadline. |
| **delegate [assignee]** | Updates `assignee` on the target record (`reassign`) while preserving the human `owner`. |
| **blocked** | Records or links an external blocker record under `blockers/` without inventing a synthetic task lifecycle state. |
| **finish / confirm plan** | Advances to Screen 3 recap (`finish`) or commits staged changes to disk (`daily_tasks_confirm_plan(confirmed=true)`). Unselected available tasks require no dates. |

## Batch isolation and recap fidelity

When a multi-item user reply contains both clear directives and an ambiguous item, unambiguous operations are staged immediately while only the ambiguous row is held for a focused clarification question. Screen 3 recaps use the validated screen layout showing today's selected work across `My work`, `Delegated work`, and `Follow-up work`, omitting future-day tables unless the user explicitly asks for a multi-day or week view.
