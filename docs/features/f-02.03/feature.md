---
id: F-02.03
group: "02"
status: implemented
---

# F-02.03 Anytime Check-In & Manual Edit Reconciliation

## Summary

Run or resume a check-in at any time of day to reconcile manual document edits, record progress updates, resolve state conflicts, and carry unfinished work forward into today's plan.

## User Need

Users need the freedom to check boxes or edit project and daily plan files directly in their editor at any point during the day, then check in later to reconcile those manual edits with project records and resolve any discrepancies without losing work.

## Conceptual Context

- [C-01: Canonical Work Records & Embedded Definition of Done](../../concepts/c-01-canonical-work-records.md) — reconciles manual checkbox and text edits in canonical records against daily plan views.
- [C-02: Local-Day Plan, Rollover & Carried Selections](../../concepts/c-02-local-day-plan-and-rollover.md) — opens or creates today's local-day plan with carry-forward and reconciles manual daily plan edits.

## Use Cases

- [UC-02.03.01: Reconcile Manual Edits and Progress During Check-In](uc-02.03.01-reconcile-manual-edits-at-checkin.md)

## Scope

- Detect manual checkbox and status edits across daily plans, project indexes, milestones, tasks, and blockers by comparing current files against canonical states and saved reconciliation baselines.
- Open today's daily plan—or create it with carried-forward unfinished work (`↺`) if missing—whenever the user checks in.
- Identify conflicts (such as a task checked done in a daily plan while Definition of Done items or blockers remain open in the task record) and prompt the user for an explicit resolution.
- Identify unlinked manual lines added to a daily plan and offer to capture them as candidate tasks or preserve them as personal notes.
- Support saving and resuming an interrupted check-in so previously confirmed decisions are not lost.

## Out of Scope

- Automatically overriding canonical record states from manual daily plan edits when completion guardrails are unmet.
- Background file-watching daemons that mutate files while the user is typing.

## Inputs

- Current workspace Markdown files (daily plans, projects, milestones, tasks, blockers) and prior reconciliation state.
- User progress reports and conflict resolution decisions during check-in.

## Outputs

- Synchronized canonical work records and today's daily plan reflecting reconciled progress.
- Resumable check-in state if interrupted, and appended decision log entries for all resolved changes.

## Acceptance

- Manual checkbox completions in a daily plan are verified against the task's Definition of Done and blockers before marking the canonical task record complete.
- Unrelated manual notes and prose added to daily plans or project records are preserved verbatim during reconciliation.
- An interrupted check-in can be resumed later without re-asking decisions that were already confirmed.

## Dependencies

- [F-00.02: Canonical Work Record Storage & Surgical Updates](../f-00.02/feature.md)
- [F-01.01: Candidate Work Capture & Deduplication](../f-01.01/feature.md)
- [F-01.02: Project, Milestone, Task & Blocker Lifecycle Management](../f-01.02/feature.md)
