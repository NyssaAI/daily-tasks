---
id: 01a1129e-f872-719b-abb5-6d2118cae1e3
type: planning-screen-template
title: "First daily check-in — select tasks"
document-maturity: reviewed
---
Open projects: {open project count}          Open tasks: {open task count}          Late tasks: {late task count}

<!-- if: first_run_today -->
This is your first check-in today. Review the work carried forward, then choose
which available tasks to add. Status marks show progress; the sections indicate
whether work is selected for today. [x] means completed, never merely selected.
<!-- endif -->

## Already selected

| #  | Status | Project | Task | Due Date |
| --- | --- | --- | --- | --- |
| 1  | [ ] | PROJECT_TITLE | ↺ [[RELATIVE_SELECTED_TASK_PATH\|TASK_TITLE]] <!-- ref: SELECTED_TASK_UUID --> | TARGET_DATE_OR_DASH |

## Available tasks

| # | Status | Project | Task | Due Date |
| --- | --- | --- | --- | --- |
| 2 | [ ] | PROJECT_TITLE | [[RELATIVE_TASK_PATH\|TASK_TITLE]] <!-- ref: TASK_UUID --> | TARGET_DATE_OR_DASH |
| 3 | [ ] | PROJECT_2_TITLE | [[RELATIVE_TASK_2_PATH\|TASK_2_TITLE]] <!-- ref: TASK_2_UUID --> | TARGET_2_DATE_OR_DASH |
| 4 | [ ] | PROJECT_TITLE | [[RELATIVE_TASK_3_PATH\|TASK_3_TITLE]] <!-- ref: TASK_3_UUID --> | TARGET_3_DATE_OR_DASH |

Legend: [ ] not started · [>] in progress · [x] completed · [-] cancelled · ↺ carried forward

## Update your plan

Give an instruction and the item numbers, for example:

- "Add 2, 3, 4 to today"
- "Move 1 to next Friday"
- "Show details for 2, 4."
- "Keep the current selections."
- "2, 4, 6 are in progress."
- "Show more tasks."
- "Show all milestones."

A bare list of numbers requires clarification about the intended action.

After selection, show the updated recap and continue to save and verify the plan.
Execution order is left to the person; do not add an ordering screen or prompt.

<!-- Interaction template, not a saved daily plan or authoritative task view.
Apply ../../skills/daily-tasks/references/response-conventions.md for numbered
replies, status meanings, batch handling and durable screen mappings. Status cells
reflect canonical work state; selection is represented by section membership.
The count line is the first visible line after frontmatter. Preserve its labels.
Conditional comments are instructions to the rendering skill, not executable
Markdown syntax. Render the enclosed introduction only when first_run_today is
true, then omit the conditional comments from the screen. Resolve first_run_today
from whether a planning session was already started on the configured local day;
do not repeat the introduction on same-day calls or resumed screens. Keep this
distinct from successful check-in completion, which remains separately tracked.
Counts describe user-owned records in the scoped inventory, not only selected rows:
- Open projects: unique projects owned by the user in not-started or in-progress state.
- Open tasks: unique tasks owned by the user in not-started or in-progress state.
- Late tasks: user-owned open tasks with an explicit target_date earlier than the configured
  local day. Tasks due today are not late. Never infer a due date.
Filter this view by canonical owner matching the current user's email, regardless
of assignee. Do not split delegated work or display assignees. Ownership permits
the user to select work and decide delegation separately; it does not start execution.
Do not show blockers, blocker counts or a Needs clarification section in this view.
Keep reconciliation conflicts in their own workflow, preserving affected selections
without presenting uncertain state as resolved. Identify incomplete/stale inventory;
do not present uncertain counts as verified exact totals.
Successful check-in completion is separate durable state for the local day;
plan-file existence alone does not prove a completed check-in. Preserve an existing plan's selections
even when there has not yet been a completed check-in today. Carry unresolved prior
selections once per local day under the planning-flow rollover protocol, including
into an existing pre-created plan. Preserve that plan's selections and explicit
removals. Only verified dated rollover state prevents repeat carry, not file existence.
Keep already-selected tasks out of available rows. Adding work moves its row into
today's selected section without changing its canonical status. New additions
require the user's supplied planning decision.
Status replies are accepted on both selected and available task rows. For example,
"2, 4, 6 are in progress" changes those identified tasks' canonical states, not
their day selections. Apply through the records operation protocol: checkpoint,
update canonical task records and required parent effects, update their project
index views, then update the daily plan. Preserve the daily plan if a project update
fails; retain the pending operation and report the exact incomplete effect.
Clarify ambiguous commands before changing affected records; never infer whether
a bare number means add, start, complete or another action.
Offer additions in project directory date order, oldest first, with alphabetical
name tie-breaking; undated directories follow alphabetically by name. Preserve
task order within each project index. Do not rank by priority, due date or lateness. For each project show only its
first incomplete milestone in the authoritative milestone sequence (skip completed
and cancelled milestones), unless the user explicitly requests all milestones.
Do not advance to a later milestone merely because the first incomplete milestone
has no eligible tasks. Existing daily selections from later milestones remain.
If source milestone order cannot be established, resolve it before relying
on "first"; do not use UUID order as milestone order.
Exclude tasks explicitly selected for future local dates from available additions,
including earlier review decisions and durable future selections. A future due date
alone does not exclude a task. Moving work to a future date does not change its due
date and does not cause it to reappear on a later page or recap today.
Show at most 15 available addition rows per screen/page. This cap does not limit
already-selected rows or change the inventory counts. Offer Show more when further
eligible rows remain; preserve stable item numbers and decisions across pages.
Remove example rows and render concise empty-state text for empty sections.
Use only #, Status, Project, Task and Due Date columns. Group rows under project/milestone
headings. Render explicit due dates as yyyy.mm.dd (for example 2026.11.12), or an
em dash when absent. Keep the Due Date column compact, sized for ten date characters
when the host allows width control. Preserve canonical target_date storage format;
this is a display-only conversion.
Keep task labels short and descriptive; full descriptions stay in task files.
Do not remove selections outside this ownership view from the underlying plan
merely because they are not displayed here.
Assign one continuous sequence across selected and available user-owned tasks.
Prefix carried-forward task titles with ↺ in the Task cell, outside the link.
Carry-forward means an unresolved selection brought from the most recent earlier
daily plan, not a task merely retained during another check-in on the same day.
Persist its source plan/date in review state so the marker survives follow-up
renders. Do not mark newly selected tasks as carried forward. The marker describes
selection provenance, not task status, priority or execution assignment.
After a response batch, recap with the same #, Status, Project, Task and Due Date
columns and original row numbers. In the daily view show today's selected work
and available unselected work only. Do not render tomorrow or other future-day
tables unless the user explicitly requests the week view. Tasks explicitly moved
to another day leave today's available list; retain their review decisions without
displaying future-day assignments in the daily recap. In week view group by local
day. Preserve carried-forward markers and actual
due dates; moving a planned day never changes a due date. Clearly label fictional
or dry-run recaps and do not claim unsupported future-day persistence succeeded.
Never restart numbering at section boundaries.
Map numbers to task UUIDs in resumable review state. Retain the
mapping across pagination and follow-up replies; do not renumber after selection
changes. Mark removed/unavailable items and give newly added items unused numbers.
Resolve replies against the displayed review before acting. Each actionable item
gets a number; headings and contextual notes refer to items but are not selections.
Validate supplied numbers and actions; retain clear decisions while clarifying
ambiguous items. Selection never completes tasks or starts delegation.
Use links suitable for the host; wiki links above exemplify readable labels.
Show the broader eligible inventory through pages of at most 15 addition options.
Make remaining eligible rows accessible via Show more and allow an explicit
all-milestones request without lifting the per-page cap. No automatic shortlist.
On later same-day requests preserve the plan and follow the requested edit/check-in
route; do not force this first-check-in selection screen again.
This draft's maturity describes the template, not resulting plans. -->
