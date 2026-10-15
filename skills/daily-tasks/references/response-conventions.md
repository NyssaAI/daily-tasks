# Planning-screen response conventions

> [!IMPORTANT]
> **Scope Directive**: This document defines the user-facing presentation, interactive numbered-reply protocol, status/action legends, review screen validation gate, and batch response parsing for Daily Tasks planning and check-in sessions. It is strictly an interaction and presentation specification. Low-level CLI commands and signatures belong in [`cli.md`](cli.md), transactional write-ahead checkpointing in [`operations.md`](operations.md), record schemas in [`records.md`](records.md), and planning domain rules, rollover algorithms, and review scope in [`planning-flow.md`](planning-flow.md).

## Required screen validation gate

Before presenting daily review options or decision recaps to the user:
1. **Read active template**: Obtain `planDayReview` layout from `packet.templates.templates.planDayReview.active.content`.
2. **Draft screen markdown**: Format the draft with exact review rows, numbered handles, and hidden `ref` comments (`[[relative-path|Task title]] <!-- ref: UUID -->`). Never present raw filesystem paths or bare UUIDs.
3. **Validate and persist**: Pass the complete draft as `reviewMarkdown` to `planning-state` action `save-review` with fresh packet hashes.
4. **Display exact output**: Render the returned `value.screen.markdown` unchanged outside code fences. Do not substitute alternate table styles, unvalidated numbered lists, or prose summaries unless explicitly specified by the template.
5. **Enforce validation**: Resolve validation failures before prompting the user for choices.

## Presentation legends and meanings

Every review screen displays standard prompt and legend lines:

```text
Reply by row number and symbol or description:

Legend: [ ] not started · [>] in progress · [x] completed · [-] cancelled
```

- When carried-forward work is present, append `· ↺ carried forward` to the legend and prefix carried task titles with `↺`.
- For blocker rows, display: `Legend: [ ] open · [x] completed (resolved)`.
- Status indicators reflect canonical task/blocker states, **not** daily plan selection. Adding a task to today preserves its lifecycle status.

### Status mapping table

| Reply / Symbol | Daily Tasks Meaning | Action Taken |
| :--- | :--- | :--- |
| `[ ]` / `not started` / `pending` | Not started | Retain or reset status via canonical records protocol. |
| `[>]` / `in progress` | In progress | Record execution start with host activity timestamp. |
| `[x]` / `complete` / `resolved` | Completed (or Blocker resolved) | Verify DoD / criteria and record completion; keep row in today's plan. |
| `[-]` / `cancel` | Cancelled | Cancel identified record; do not silently cascade to parent. |

## Numbered-reply protocol

- **Continuous sequence**: Start tables with `#` and number actionable rows in a single continuous 1-based sequence across the screen. Headings and summary lines are not numbered.
- **Stable handles**: Row numbers are transient session response handles, not priority ranks or record IDs. Keep mappings stable across refreshes and pages. Never renumber processed rows or reuse numbers within a session.
- **Workspace binding**: Save the number-to-UUID mapping to `stateRoot/review/YYYY.MM.DD.json` with `mappingBinding`. Never apply numbered replies from one workspace to another.
- **Accepted input formats**: Parse symbols with or without brackets, row lists, and natural language (e.g. `1 x, 2 >, 3 cancel`, `add 2, 4`, `2 delegate to Alex`).
- **Ambiguous input**: A bare number without an action is not an instruction; prompt for the user's intended action.
- **Collective reports**: Apply collective updates (e.g. `2, 4, 6 in progress`) to each identified task record, updating canonical records and parent effects before updating daily plan projections.

## Planning actions reference

- **add / today**: Select accepted tasks for today's plan without altering lifecycle state, target date, or assignment.
- **remove**: 
  - For `not-started` work: deselect from today and clear carry-forward without requiring a reschedule date.
  - For `in-progress` work: requires an explicit reschedule date, completion, or cancellation; prompt for missing disposition.
- **keep**: Retain current selections and statuses; omitted rows remain untouched.
- **show details**: Display the full requirements, DoD, and context for the identified record.
- **next / show more**: Advance to the next project page of eligible tasks. Keep each project contiguous, preserving stable numbers and earlier selections. Display page indicators (`Page X of Y`).
- **previous**: Return to the preceding project page using the saved mapping (enabled when `page > 0`).
- **show all milestones**: Display later milestone tasks for inspection without making them eligible for selection (eligibility remains bound to the lowest incomplete milestone).
- **later / defer [date]**: Remove `not-started` work from today. For explicit future dates, execute the future-selection transaction (create target daily plan, update `removedIds`, maintain exactly one active date per task). Never alter `target_date`.
- **delegate [assignee]**: Update `assignee` in task metadata; preserves human `owner`.
- **blocked**: Record or link a blocker via records; does not introduce an artificial task status.
- **confirm plan**: Finalize displayed selections and commit the daily plan. Unselected available tasks do not require dates.

## Response processing and recaps

- **Batch isolation**: Process unambiguous items in a batch. If an item is ambiguous, suspend only that item, ask a focused clarification question, and retain already-decided items.
- **Feedback & echoes**: Acknowledge decisions briefly using their original row numbers, noting any unresolved questions.
- **Recap presentation**: Present daily plan recaps using the same layout as the source screen, showing today's selected work and remaining available options. Omit future-day tables unless an explicit multi-day/week view is requested.
