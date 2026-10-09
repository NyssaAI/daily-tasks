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

| #  | Status | Project | Milestone | Task | Due Date |
| --- | --- | --- | --- | --- | --- |
| 1  | [ ] | PROJECT_TITLE | MILESTONE_TITLE | ↺ [[RELATIVE_SELECTED_TASK_PATH\|TASK_TITLE]] <!-- ref: SELECTED_TASK_UUID --> | TARGET_DATE_OR_DASH |

## Available tasks

| # | Status | Project | Milestone | Task | Due Date |
| --- | --- | --- | --- | --- | --- |
| 2 | [ ] | PROJECT_TITLE | MILESTONE_TITLE | [[RELATIVE_TASK_PATH\|TASK_TITLE]] <!-- ref: TASK_UUID --> | TARGET_DATE_OR_DASH |
| 3 | [ ] | PROJECT_2_TITLE | MILESTONE_2_TITLE | [[RELATIVE_TASK_2_PATH\|TASK_2_TITLE]] <!-- ref: TASK_2_UUID --> | TARGET_2_DATE_OR_DASH |
| 4 | [ ] | PROJECT_TITLE | MILESTONE_TITLE | [[RELATIVE_TASK_3_PATH\|TASK_3_TITLE]] <!-- ref: TASK_3_UUID --> | TARGET_3_DATE_OR_DASH |

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
Before deriving rows/counts or rollover, load ../references/planning-flow.md,
especially Build and review, Review scope and Once-per-day rollover. Before
waiting/interpreting replies or recapping, load ../references/response-conventions.md
for status meanings, stable durable mappings, batch handling and today-only recaps.
Before status/record writes or recovery, load ../references/operations.md.
For supplied/configured formatting load ../references/templates.md; this asset is
the bundled default, not an override of user formatting.

The count line is the first visible line after frontmatter. Preserve its labels.
Conditional comments instruct the rendering skill, not executable Markdown syntax.
Render the introduction only for first_run_today, then omit conditional comments.
Use the planning-flow review state, not plan existence or completed-check-in state.
Remove example rows and render concise empty-state sentences for empty sections.
Use only #, Status, Project, Milestone, Task and Due Date columns. Group rows under
project/milestone headings; never restart numbering at section boundaries.
Show each task's owning milestone as plain text, even under grouped headings;
it is not a separate selectable/status row. Task links/hidden refs identify tasks.
Keep task labels short and descriptive; full descriptions remain in task files.
Use host-suitable links with readable labels and escape wiki label pipes.
Render explicit due dates as yyyy.mm.dd (for example 2026.11.12), or an em dash when
absent. Keep Due Date compact, sized for ten date characters when supported.
Canonical target_date format is unchanged; planned-day moves never change due dates.
Status cells show canonical work progress; sections show day selection.
Prefix carried-forward titles with the carry marker in the Task cell, outside the
link, using recorded source-plan/date provenance under response conventions.
Clearly label fictional/dry-run output; template maturity describes this template,
not resulting plans. -->
