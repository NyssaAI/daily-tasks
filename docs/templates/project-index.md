---
id: PROJECT_UUID
type: project
title: "PROJECT_TITLE"
document-maturity: reviewed
project-state: not-started
owner: "OWNER_EMAIL"
created_at: "GMT_TIMESTAMP"
updated_at: "GMT_TIMESTAMP"
---
# PROJECT_TITLE

One sentence describing the outcome this project will deliver and who benefits.

**State:** Not started  
**Owner:** OWNER_NAME  
**Updated:** LOCAL_DISPLAY_TIME_WITH_ZONE

## Outcome

Describe what will be different when this project is complete. Keep this focused
on the result, with enough detail to recognize success.

## Project Summary

| Milestone | Task | Description | Owner | Due Date |
| --- | --- | --- | --- | --- |
| [ ] [[MILESTONE_SLUG/MILESTONE_SLUG\|M1 — MILESTONE_TITLE]] <!-- ref: MILESTONE_UUID --> | | The concrete outcome this milestone will deliver. | MILESTONE_OWNER_NAME | MILESTONE_TARGET_DATE |
| | [ ] [[MILESTONE_SLUG/TASK_SLUG\|M1-T1 — TASK_TITLE]] <!-- ref: TASK_UUID --> | The action to take and its intended output. | TASK_OWNER_NAME | TASK_TARGET_DATE |
| [ ] [[MILESTONE_2_SLUG/MILESTONE_2_SLUG\|M2 — MILESTONE_2_TITLE]] <!-- ref: MILESTONE_2_UUID --> | | The concrete outcome of the second milestone. | MILESTONE_2_OWNER_NAME | MILESTONE_2_TARGET_DATE |
| | [ ] [[MILESTONE_2_SLUG/TASK_2_SLUG\|M2-T1 — TASK_2_TITLE]] <!-- ref: TASK_2_UUID --> | The action to take and its intended output. | TASK_2_OWNER_NAME | TASK_2_TARGET_DATE |

## Blocked by

| Blocker | Impact | Owner | Resolved When |
| --- | --- | --- | --- |
| [ ] [[blockers/BLOCKER_SLUG\|B1 — BLOCKER_TITLE]] <!-- ref: BLOCKER_UUID --> | The milestone or task that cannot proceed. | BLOCKER_OWNER_NAME | The condition or evidence that removes the impediment. |
| [ ] [[blockers/BLOCKER_2_SLUG\|B2 — BLOCKER_2_TITLE]] <!-- ref: BLOCKER_2_UUID --> | The affected work and consequence. | BLOCKER_2_OWNER_NAME | The condition or evidence that removes the impediment. |

## Decisions

- **Decision needed:** State the choice, who must make it, and what it affects.

## Notes and references

Keep supporting context here. Link to source material and individual task files
instead of duplicating their full instructions.

<!-- Formatting example only. Replace sample content and placeholders with actual
accepted records. Repeat milestone/task rows as needed. Definitions of done remain
in their owning milestone and task files, not this index.
M1 and M1-T1 are readable labels, not record identities; retain UUID refs
and actual relative links. Escape wiki-link label pipes inside table cells.
Due Date displays an explicitly supplied target_date; use an em dash when absent.
Owner displays the human owner; identify a different assignee in the description
when relevant. Display state/owner/update values are projections of canonical metadata.
Use short empty-state sentences where there are no milestones, blockers or decisions.
Preserve headings needed for relationship recognition.
Table/list status projections are parsed by identity. Reconcile editable status
changes against the stored per-view baseline before refreshing this index. -->
