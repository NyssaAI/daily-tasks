---
id: F-00.02
group: "00"
status: implemented
---

# F-00.02 Canonical Work Record Persistence & Non-Destructive Updates

## Summary

Read and update editable project, milestone, task, blocker, and daily plan documents while preserving user-authored notes, comments, and layout formatting intact.

## User Need

Users need to edit their project, milestone, task, blocker, and daily plan files freely in any text editor or knowledge vault knowing that assistant-driven updates will modify only the adjudicated fields and checkboxes without destroying personal notes or custom formatting.

## Conceptual Context

- [C-01: Canonical Work Records & Embedded Definition of Done](../../concepts/c-01-canonical-work-records.md) — parses and non-destructively writes Project, Milestone, Task, and Blocker records without losing user edits.
- [C-02: Local-Day Plan, Rollover & Carried Selections](../../concepts/c-02-local-day-plan-and-rollover.md) — reads prior daily plans and writes the confirmed daily plan document.
- [C-04: Three-Screen Planning Session Macro-Flow](../../concepts/c-04-three-screen-planning-session.md) — loads the initial vault snapshot and atomically persists staged record edits and the daily plan upon confirmation.

## Use Cases

None yet.

## Scope

- Read project indexes, milestones, tasks, external blockers, and dated daily plans from the configured vault into validated domain records.
- Skip and report individual malformed files diagnostically without failing the entire vault load.
- Non-destructively apply adjudicated updates (status changes, Definition of Done checkbox toggles, assignee/owner updates, target dates, and new rows) while preserving all unrelated text, comments, and whitespace byte-for-byte.
- Render and write dated daily plan documents listing personal work, delegated work, active blockers, and decisions.
- Verify that underlying files have not been modified externally since the session snapshot before committing batch changes, writing all files atomically.

## Out of Scope

- Deciding which tasks or suggestions should be accepted or planned (owned by [F-01.01](../f-01.01/feature.md), [F-02.01](../f-02.01/feature.md), and [F-02.02](../f-02.02/feature.md)).
- Fetching messages from external email or chat services (owned by [F-00.03](../f-00.03/feature.md)).

## Inputs

- Existing project, milestone, task, blocker, and daily plan documents in the configured vault.
- Validated, user-adjudicated record changes, decision log entries, and daily plan selections.

## Outputs

- Parsed vault records and content fingerprints ready for planning and check-in workflows.
- Non-destructively updated project, milestone, task, and blocker files with unrelated user content preserved.
- Newly written or updated `YYYY.MM.DD-daily-plan.md` files in the vault and append-only decision log records in the runtime state folder.

## Acceptance

- Reading and re-saving a record after a targeted status or checkbox update leaves all unrelated lines, user notes, and comments byte-for-byte identical.
- If any target record file was modified outside the session after the snapshot was taken, the batch write is refused cleanly and no files are partially overwritten.
- Generated daily plan documents accurately reflect selected personal tasks, delegated tasks, carried-forward markers (`↺`), and active blockers.

## Dependencies

- [F-00.01: Vault, Identity & Template Setup](../f-00.01/feature.md)
