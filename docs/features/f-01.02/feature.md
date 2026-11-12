---
id: F-01.02
group: "01"
status: implemented
---

# F-01.02 Project, Milestone, Task & Blocker Lifecycle Management

## Summary

Create accepted projects, milestones, tasks, and external blockers; manage Definitions of Done, ownership, delegation, target dates, and dependencies; and enforce completion rules before closing work.

## User Need

Users need structured records for projects, milestones, tasks, and external blockers so they can track both their own work and delegated commitments, verify that every Definition of Done item and blocker is satisfied before marking work complete, and keep a clear decision history of changes.

## Conceptual Context

- [C-01: Canonical Work Records & Embedded Definition of Done](../../concepts/c-01-canonical-work-records.md) — creates records and enforces status, Definition of Done, delegation, and blocker completion rules.
- [C-03: Explicit Adjudication & Decision Log](../../concepts/c-03-explicit-adjudication-and-decision-log.md) — validates state changes and completion rules before applying adjudicated record mutations.

## Use Cases

- [UC-01.02.01: Update Task Status, Definition of Done & Blockers](uc-01.02.01-update-work-status-and-dod.md)

## Scope

- Create accepted projects, milestones, tasks, and external blockers using active vault templates.
- Update lifecycle states (`not-started`, `in-progress`, `completed`, `cancelled` for projects/milestones/tasks; `open` and `resolved` for blockers).
- Manage embedded Definition of Done checklist criteria within milestones and tasks.
- Assign and update ownership, delegation (assignee), optional target dates, task dependencies (`Depends on` / `Required by`), and blocker links (`Blocked by`).
- Enforce completion guardrails: require all Definition of Done items checked and all linked blockers resolved before completing a task, and require all child tasks finished (or explicitly decided) before completing or cancelling a milestone.
- Record all lifecycle mutations in the append-only decision log.

## Out of Scope

- Selecting which tasks to work on for a specific calendar day (owned by [F-02.02](../f-02.02/feature.md)).
- Estimating task durations or scheduling tasks into calendar time slots.

## Inputs

- Direct user instructions to create named work or accepted candidates from [F-01.01](../f-01.01/feature.md) / [F-02.01](../f-02.01/feature.md).
- Requested updates to status, Definition of Done items, assignee, owner, target date, dependencies, or blockers.

## Outputs

- Created or non-destructively updated Project, Milestone, Task, and Blocker documents with synchronized parent index tables.
- Validation messages explaining any unmet Definition of Done criteria or open blockers when completion is refused.
- Appended decision log entries for every applied change.

## Acceptance

- A direct instruction to create named work creates the record immediately without a redundant confirmation prompt.
- Attempting to mark a task complete while any Definition of Done item is unchecked or any linked blocker is open is refused with a message naming the unmet requirements.
- Completing or cancelling a milestone with open tasks requires an explicit decision for each open task and never cascades cancellation silently.
- Delegating a task to another person preserves the user as owner so the task appears under Delegated work when planned.

## Dependencies

- [F-00.01: Vault, Identity & Template Setup](../f-00.01/feature.md)
- [F-00.02: Canonical Work Record Persistence & Non-Destructive Updates](../f-00.02/feature.md)
