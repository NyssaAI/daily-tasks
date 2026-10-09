# Planning-screen response conventions

Use these conventions for every Daily Tasks planning/review screen and follow-up.
Preserve the current screen template and its ownership filter. The interaction
sequence uses the selected screen layout and the
[planning-flow contract](planning-flow.md#build-and-review); load it before saving
a planning mapping, deriving eligibility or applying rollover/future selections.
Load [operations](operations.md) before record/status effects or recovery. Do not
import another plugin's process.

## Legends and meanings

Every screen displays these two lines:

Reply by row number and symbol or description:

Legend: [ ] not started · [>] in progress · [x] completed · [-] cancelled

This legend describes work status. `[x]` always means completed (resolved for a
blocker), never day selection. Put marks in Status cells; represent selection by
the selected/available sections. Adding a row to today preserves its work state.
Keep screen-specific planning actions separate, for example:
`add 2, 3 · remove 1 · show details for 4 · keep selections`.
When a screen includes carried-forward selections, append `· ↺ carried forward`
to its legend and prefix those task titles with ↺. This marks selection provenance
from the most recent earlier plan; it is not another lifecycle state. Preserve the
source plan/date and marker throughout the review; same-day retained work and newly
selected work do not acquire the marker solely from another screen render.

| Reply | Meaning in Daily Tasks |
| --- | --- |
| `[ ]` / not started / pending | Canonical not-started. Reopening existing work must follow the canonical reopening rules; do not erase a known start or history. |
| `[>]` / in-progress | The user reports that execution started; record timing under the records protocol. Selecting today does not mean starting. |
| `[x]` / complete | The user reports completion; validate and apply through records, preserving the row for today. |
| `[-]` / cancel | Cancel the identified task through records; retain history and do not cancel parents implicitly. |

The canonical work lifecycle is not-started, in-progress, completed and cancelled.
Delegation uses assignee and is a separate natural-language action, not a status
symbol. Preserve the human owner; ask for the assignee only when unknown. Selecting
work or delegating it does not start execution. Review/failure reports remain
context requiring the owning workflow, not additional canonical state values.

For blocker rows use `Legend: [ ] open · [x] completed (resolved)`. A numbered `[x]`,
complete or completed reply resolves the blocker through the records protocol,
storing `blocker-state: resolved`; `[ ]` or reopen maps to open and applies ancestor
reopening rules. Do not automatically complete affected tasks or parents. Blockers
have no in-progress or cancelled state. Interpret symbols by the referenced record
type, and retain blocker resolution conditions and timing.

## Numbered replies

- Start tables with # and number data rows/actionable list items in one continuous
  sequence across the screen. Headings are not items.
- Persist the active screen and number-to-record-ID mapping before waiting.
  Save its local date and mappingBinding with the active vault context. Reject a
  different vault's screen; never reinterpret its numbers against this inventory.
  Numbers are response handles, not priorities or record IDs.
- Keep mappings stable across replies, refreshes and pages. Do not renumber after
  a row is handled or reuse its number for a different item. New items get new numbers.
- On a new screen display its new mapping; clarify stale/ambiguous references.
- Accept symbols with or without brackets, numbered lists, separate lines and
  natural language: `1 x, 2 >, 3 cancel`, `add 2, 4`, or `2 delegate to Alex`.
- A bare number/list is not an instruction. Ask which action the user intends.
- Resolve actions by row type; a project or non-task row is not automatically a task.
- Accept collective status reports such as `2, 4, 6 are in progress` and apply the
  same explicit state change to each identified task. This does not select them for
  today. Through the operation protocol update canonical task records, required
  parent effects and project views before refreshing daily-plan views. A failure
  retains the checkpoint and cannot be reported as a completed batch.

## Planning actions

- **add / today:** Select identified accepted tasks for today. Do not change task
  state, target date, ownership or execution assignment.
- **remove:** Deselect from the day, stopping automatic carry-forward; keep the task
  open. Do not require another date or replacement selection.
- **keep:** Preserve current selections/state; omitted rows remain unchanged.
- **show details:** Read and display the identified record's relevant context.
- **show more:** Show the next page of eligible additions, at most 15 rows; preserve
  project/task order, earlier decisions and stable numbers.
- **show all milestones:** Expand addition eligibility to all incomplete milestones
  while retaining project/task order, the 15-row page cap and future-selection exclusions.
- **later / defer:** Remove from today's selection when clearly requested. If a
  future day is explicitly supplied, resolve and echo its local date and follow
  the [future-selection transaction](planning-flow.md#future-selection-transaction).
  Create that day's missing daily plan and preserve one active date per task.
  An explicit move transfers the active selection; a conflicting add requires
  clarification. Verify persisted effects before claiming success. Never alter target dates.
- **blocked:** Route an explicit blocker report through records; it is not a new
  task status. The ownership-only selection screen does not display blocker details.
- **remind:** Prepare a draft if requested; sending requires explicit authorization.
- **confirm plan:** Accept displayed selections and finish authorized saving.
  Unselected tasks do not need dates. Confirmation is not acceptance of new tasks,
  permission to send, or resolution of conflicts.
Do not ask the user to rank selections or review execution order. Preserve stable
display order and response handles; list position does not prescribe execution.

Process clear items in a batch and retain their decisions. Ask one focused question
for an ambiguous item, suspending only affected changes; do not silently reinterpret
unknown numbers. Silence or omitted rows never supply acceptance or completion.
Save each response batch and resume the unfinished screen after interruption.
Briefly echo results by their original numbers, with unresolved questions or failed
effects. Recap planning selections using the same table layout as the source screen.
Daily recaps show today's selected and still-available work, with no tomorrow or
future-day tables. Display future-day assignments only on an explicit week-view
request, grouped by local day. Preserve decisions for work moved out of today without
relisting it as available today. Retain original row numbers, due dates and carry
markers. A dry run changes no vault records and must not claim persistence.
