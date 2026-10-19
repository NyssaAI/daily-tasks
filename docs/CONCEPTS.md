# Concepts

> Shared domain vocabulary for this project — entities, named processes, and status concepts with project-specific meaning. Seeded with core domain vocabulary, then accretes as ce-compound and ce-compound-refresh process learnings; direct edits are fine. Glossary only, not a spec or catch-all.

## Planning & Daily Execution

### Daily Plan
A dated markdown record (`YYYY.MM.DD-daily-plan.md`) capturing the user's selected tasks for a single calendar day without duration-fitting, schedule-blocking, or automated time allocation.
*Avoid:* Schedule, daily agenda, calendar entry

A Daily Plan is an editable checklist view of accepted work. Tasks selected for the day remain bound to their canonical project records; selection or completion in a daily plan propagates verification and state changes without modifying project boundaries.

### Rollover
The once-per-day carry-forward of uncompleted or in-progress selections from the nearest earlier daily plan into the current day's plan.
*Avoid:* Reschedule, automatic rollover, deferral

Rollover executes deterministically during daily planning preparation. In-progress work and unfinished prior selections are proposed for carry-forward unless explicitly removed by the user.

### Carried Selection
A task entry in a daily plan carried forward from a previous day's plan, designated in markdown by the `↺` marker.
*Avoid:* Rolled task, postponed item

Carried Selections retain provenance to the originating plan date (`carriedFrom`). When a daily plan is authored with `↺` entries, verification validates that the carried items match the proposed rollover candidates before saving state.

### Planning Review
A numbered review screen presenting rollover candidates, available tasks from active milestones, and diagnostic items for user selection.
*Avoid:* Daily dashboard, planning triage

The Planning Review generates ephemeral mapping numbers for selection commands, enabling fast batch interaction without requiring the user or agent to type full UUIDs or file paths.

### Definition of Done (DoD)
The checklist criteria defining the completion requirements for a milestone or task.
*Avoid:* Acceptance criteria file, DoD document

Criteria are canonically embedded within the task or milestone record under a `## Definition of Done` heading. Each criterion carries a stable identity comment (`<!-- id: UUID -->`).

## Retired

- **Standalone Definition of Done (DoD)**: An obsolete separate markdown record type (`type: dod`) previously linked from milestones; removed in favor of embedded checklist criteria.
- **Milestone Workspace Migration**: A transitional workflow and CLI command set used to migrate standalone DoD files into embedded task criteria; retired after repository-wide adoption.
