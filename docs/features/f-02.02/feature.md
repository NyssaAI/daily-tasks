---
id: F-02.02
group: "02"
status: implemented
---

# F-02.02 Three-Screen Daily Planning & Day Assignment

## Summary

Guide the user through reviewing today's carried-forward work and message suggestions (Screen 1), assigning open project tasks and blocker follow-ups to specific days (Screen 2), and confirming the final daily plan (Screen 3) with full decision logging.

## User Need

Users need a fast, predictable daily planning ritual that carries forward unfinished work, walks through active projects one by one using stable row numbers for quick batch replies, separates personal tasks from delegated work, and writes an editable daily plan without trying to schedule hours on a calendar.

## Conceptual Context

- [C-02: Local-Day Plan, Rollover & Carried Selections](../../concepts/c-02-local-day-plan-and-rollover.md) — displays carried-forward selections, assigns tasks and blockers to today or future days, and confirms the daily plan.
- [C-03: Explicit Adjudication & Decision Log](../../concepts/c-03-explicit-adjudication-and-decision-log.md) — adjudicates suggestions, executes numbered planning operations, and appends entries to the decision log.
- [C-04: Three-Screen Planning Session Macro-Flow](../../concepts/c-04-three-screen-planning-session.md) — manages the Screen 1 → Screen 2 → Screen 3 state machine, row numbering, and confirmation flow.

## Use Cases

- [UC-02.02.01: Assign Open Project Tasks & Blockers to Days on Screen 2](uc-02.02.01-assign-project-tasks-to-days.md)
- [UC-02.02.02: Review Recap and Confirm Today's Plan on Screen 3](uc-02.02.02-confirm-and-write-daily-plan.md)

## Scope

- Carry unfinished task and blocker selections forward (`↺`) from the nearest earlier daily plan into Screen 1's Current Plan view.
- Present open projects one per screen on Screen 2, ordered with projects containing unplanned eligible work first.
- Maintain one continuous, fixed 1-based row numbering sequence across Screens 1 and 2, and restart row numbering at `1` on Screen 3's final recap.
- Support batch operations on Screen 2 and Screen 3: planning items for Today or a future date, unplanning items, assigning/delegating tasks, changing task/milestone/blocker status, and toggling whether all in-progress milestones or only the lowest incomplete milestone are shown.
- Render Screen 3's today-only recap grouped into **My work**, **Delegated work**, and **Blockers**, warn about any unanswered suggestions, and commit all staged record changes, decisions, and `YYYY.MM.DD-daily-plan.md` atomically upon confirmation.

## Out of Scope

- Fitting tasks into calendar time blocks, estimating durations, or ranking execution order within the day.
- Structural project reorganization (such as rewriting Definition of Done prose or moving tasks between milestones) during day assignment on Screen 2.

## Inputs

- Workspace state graph (projects, milestones, tasks, blockers, and recent daily plans) and pending suggestions.
- User navigation commands (`yes`, `next`, `previous`, `finish`, `Back to <Project>`, `Confirm`, or `cancel`) and numbered batch operations.

## Outputs

- Rendered Markdown screens for Screen 1 (Plan the Day), Screen 2 (Assign Tasks to Days per Project), and Screen 3 (Confirm Today's Plan).
- Staged record mutations, appended decision log entries, pruned suggestion buffer, and the confirmed `YYYY.MM.DD-daily-plan.md` file.

## Acceptance

- Row numbers assigned on Screens 1 and 2 never change across refreshes or project pagination, and Screen 3 restarts numbering at `1` while rejecting stale numbers from Screens 1 and 2.
- Planning a task for Today or a future date updates its single active planned day without altering its target due date or task status.
- Confirming on Screen 3 writes `YYYY.MM.DD-daily-plan.md` and all staged record updates atomically; cancelling discards the session without modifying any disk files.

## Dependencies

- [F-00.02: Canonical Work Record Storage & Surgical Updates](../f-00.02/feature.md)
- [F-01.02: Project, Milestone, Task & Blocker Lifecycle Management](../f-01.02/feature.md)
- [F-02.01: Communication Correlation & Update Suggestions](../f-02.01/feature.md)
