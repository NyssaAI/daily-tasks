---
id: C-02
type: domain-model
status: active
---

# C-02: Local-Day Plan, Rollover & Carried Selections

## Summary

A Daily Plan is a dated, editable document (`YYYY.MM.DD-daily-plan.md`) that captures the tasks and blocker follow-ups selected for a single local calendar day without estimating durations or fitting work into time slots. Unfinished selections from the most recent prior daily plan are carried forward once per day (`↺`) so nothing is silently dropped between days.

## Core Model / Stages

- **Daily Plan**: A local-day view resolved in the user's configured timezone. Groups selected tasks into **My work** (assigned to the user) and **Delegated work** (owned by the user, assigned to another person), alongside an **Active Blockers** table for open blockers affecting today's tasks or scheduled for follow-up today, and a **Decisions** log summary.
- **Rollover**: The deterministic once-per-day preparation step that inspects the nearest earlier daily plan and proposes any uncompleted (`not-started` or `in-progress`) selections for carry-forward into today's plan.
- **Carried Selection (`↺`)**: A daily plan entry carried forward from a prior day's plan. It displays the `↺` prefix in plan tables and retains provenance to the originating plan date (`carriedFrom`).
- **Single Active Planned Day**: Each open task or blocker has at most one active planned day on or after today (`Today`, a specific future date, or unplanned `—`). Reassigning an item to a new day moves its planned day without altering its target due date.

## Invariants & Rules

- **Zero Time-Fitting**: Daily plans never assign hours, time blocks, duration estimates, or automatic execution order; the user decides the order of execution.
- **Selection Does Not Mutate Task State**: Adding, carrying forward, moving, or removing a task on a daily plan changes only its day selection and never implicitly starts, completes, or cancels the underlying task record.
- **Blocked Work Can Be Planned**: Tasks with open blockers display a warning indicator (`⛔`) so the user can see the impediment, but they are not barred from being planned for a day.
- **Future Selections Hide from Today's Additions**: Tasks already planned for a future date are excluded from today's unplanned additions unless the user explicitly moves them back to today.

## Participating Features

- [F-00.01: Workspace, Identity & Template Setup](../features/f-00.01/feature.md) — configures the user's local timezone and daily plan template.
- [F-00.02: Canonical Work Record Storage & Surgical Updates](../features/f-00.02/feature.md) — reads prior daily plans and writes the confirmed daily plan document.
- [F-02.02: Three-Screen Daily Planning & Day Assignment](../features/f-02.02/feature.md) — displays carried-forward selections, assigns tasks and blockers to today or future days, and confirms the daily plan.
- [F-02.03: Anytime Check-In & Manual Edit Reconciliation](../features/f-02.03/feature.md) — opens or creates today's local-day plan with carry-forward and reconciles manual daily plan edits.
