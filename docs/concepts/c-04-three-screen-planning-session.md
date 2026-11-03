---
id: C-04
type: flow
status: active
---

# C-04: Three-Screen Planning Session Macro-Flow

## Summary

The Daily Tasks planning session guides the user from initial state collection and background message correlation through three structured interactive screens—**Screen 1 (Plan the Day & Suggested Updates)**, **Screen 2 (Assign Tasks to Days per Project)**, and **Screen 3 (Confirm Today's Plan)**—before atomically persisting all staged record updates and writing today's daily plan.

## Core Model / Stages

```text
"Let's plan the day"
  |
  +-- Stage 0: Collect Current State & Start Background Message Analysis
  |     +-- Read projects, milestones, tasks, blockers, and recent daily plans into an in-memory State Graph
  |     \-- Fetch unread email/chat messages since last cursor, correlate with open work, and draft suggestions
  |
  +-- Stage 1 (Screen 1): Plan the Day & Adjudicate Suggestions
  |     +-- Show headline counts, carried-forward selections (↺), and numbered message suggestions (1..N)
  |     +-- User accepts, edits, or rejects suggestions and updates current selections
  |     \-- Handoff trigger: User replies "yes" to review open projects and tasks
  |
  +-- Stage 2 (Screen 2): Assign Tasks to Days (One Project per Screen)
  |     +-- Present open projects in priority order (projects with unplanned eligible work first)
  |     +-- Continue session row numbering (N+1..) across plannable milestone tasks and project blockers
  |     +-- User assigns items to Today or future dates, delegates work, or updates task/milestone/blocker status
  |     \-- Handoff trigger: User steps through projects ("next"/"previous") and replies "finish" or "yes" on last project
  |
  +-- Stage 3 (Screen 3): Confirm Today's Plan Recap
  |     +-- Restart row numbering at 1 for today's recap (My work, Delegated work, and today's Blockers)
  |     +-- Warn if any suggestions remain unanswered (they stay pending for next session)
  |     +-- Allow lightweight final adjustments (remove from today, move to tomorrow, status/assignee tweaks)
  |     \-- Handoff trigger: User replies "Confirm"
  |
  \-- Stage 4 (Confirmed): Atomic Persistence
        +-- Verify no underlying record file changed on disk since session snapshot
        \-- Write staged record updates, append decision log entries, prune acted suggestions, update cursors, and write YYYY.MM.DD-daily-plan.md
```

## Invariants & Rules

- **Stage-Gated Transitions**: Session operations are valid only in their designated stage (`INIT` → `SCREEN_1` → `SCREEN_2` → `SCREEN_3` → `CONFIRMED` or `CANCELLED`). Out-of-order requests are refused with guidance naming the expected next step.
- **Screen-Scoped Row Numbering**: Screens 1 and 2 share one continuous, monotonic 1-based row sequence so row numbers never shift as suggestions arrive or as the user pages between projects. Screen 3 restarts numbering at `1` for the final recap and rejects stale row numbers from Screens 1 and 2.
- **Staged Writes Until Confirmation**: Decisions and record edits made during Screens 1–3 update the in-memory session graph and remain staged until the user confirms on Screen 3. Cancelling a session discards staged changes without touching disk records.
- **Optimistic Concurrency Protection**: Before applying staged record changes on confirmation, each target file's content hash is verified against the session snapshot; any external modification aborts the write cleanly so manual edits are never overwritten.

## Participating Features

- [F-00.02: Canonical Work Record Storage & Surgical Updates](../features/f-00.02/feature.md) — loads the initial workspace snapshot and atomically persists staged record edits and the daily plan upon confirmation.
- [F-00.03: Credential Privacy & Read-Only Communication Connections](../features/f-00.03/feature.md) — supplies incremental unread emails and chat messages during Stage 0 without blocking the session start.
- [F-02.01: Communication Correlation & Update Suggestions](../features/f-02.01/feature.md) — correlates ingested messages against the state graph to populate Screen 1's suggested updates.
- [F-02.02: Three-Screen Daily Planning & Day Assignment](../features/f-02.02/feature.md) — manages the Screen 1 → Screen 2 → Screen 3 state machine, row numbering, and confirmation flow.
- [F-03.02: Planning Session Tool Service & Syndication](../features/f-03.02/feature.md) — exposes the session stages as structured tool calls for AI assistant hosts.
