---
id: PLAN_UUID
type: daily-plan
title: "Daily plan LOCAL_DATE"
document-maturity: reviewed
timezone: "IANA_TIMEZONE"
created_at: "GMT_TIMESTAMP"
updated_at: "GMT_TIMESTAMP"
---
# Daily plan — LOCAL_DATE

Open projects: {open project count}          Open tasks: {open task count}          Late tasks: {late task count}

**Timezone:** IANA_TIMEZONE  
**Updated:** LOCAL_DISPLAY_TIME_WITH_ZONE

## Focus

FOCUS_DESCRIPTION

## Selected for today

### My work

#### PROJECT_TITLE / MILESTONE_TITLE

| # | Status | Project | Milestone | Task | Due Date |
| --- | --- | --- | --- | --- | --- |
| 1 | [ ] | PROJECT_TITLE | MILESTONE_TITLE | ↺ [[RELATIVE_TASK_PATH\|TASK_TITLE]] <!-- ref: TASK_UUID --> | TARGET_DATE_OR_DASH |

### Delegated work

#### DELEGATED_PROJECT_TITLE / DELEGATED_MILESTONE_TITLE

| # | Status | Project | Milestone | Task | Due Date |
| --- | --- | --- | --- | --- | --- |
| 2 | [ ] | DELEGATED_PROJECT_TITLE | DELEGATED_MILESTONE_TITLE | [[RELATIVE_DELEGATED_TASK_PATH\|DELEGATED_TASK_TITLE]] <!-- ref: DELEGATED_TASK_UUID --> | TARGET_DATE_OR_DASH |

Legend: [ ] not started · [>] in progress · [x] completed · [-] cancelled · ↺ carried forward

## Blockers

| Blocker | Impact | Owner | Resolved When |
| --- | --- | --- | --- |
| BLOCKER_TITLE | Impact on selected work. | BLOCKER_OWNER_NAME | Resolution condition. |

## Decisions

## Notes and references

<!-- Formatting example only. Before deriving counts/responsibility or saving,
load ../references/planning-flow.md, especially Review scope and Saved daily plan.
Before consequential writes/recovery load ../references/operations.md. For custom
formatting load ../references/templates.md. Replace sample content/placeholders
with actual selected work; template examples never create/select work.

Use #, Status, Project, Milestone, Task and Due Date columns. Group by project and
milestone within My work and Delegated work. Each task's owning milestone is plain
text in the Milestone cell, even under grouped headings; it is not a separate
selection/status row. One status cell and hidden ref identify each task row.
Keep task labels short, escape wiki label pipes and keep the hidden ref in Task.
Reuse review numbers continuously across sections; without a review mapping use
one continuous display sequence in the user's chosen order. Load
../references/response-conventions.md for status, response handles and carry meaning.
Prefix only recorded carry selections with the carry marker outside the task link.
Render explicit target dates as yyyy.mm.dd or an em dash; keep Due Date compact.
Omit unsupplied Focus and blank sample rows. Use short empty-state sentences for
empty work/decision/blocker sections. Keep blockers informational without task refs
or status checkboxes. Preserve completed/cancelled visibility and unresolved refs.
Do not invent focus, deadlines, estimates or scheduled slots. -->
