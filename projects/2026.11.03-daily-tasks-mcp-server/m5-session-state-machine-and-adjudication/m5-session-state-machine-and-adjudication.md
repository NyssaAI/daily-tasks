---
id: 019a4b2c-2000-7000-8000-000000000006
type: milestone
record_version: 2
title: "Session State Machine & Adjudication"
milestone-state: not-started
project_id: "019a4b2c-2000-7000-8000-000000000001"
created_at: "2026-11-03T11:30:00Z"
updated_at: "2026-11-03T11:30:00Z"
started_at: null
resolved_at: null
target_date: "2026-12-05"
tags: ["state-machine", "adjudication", "screens", "sessions", "decision-log"]
---
# [ ] M5: Session State Machine & Adjudication · 2026-12-05

**Project:** [[../project-index|Daily Tasks Python MCP Server]] <!-- ref: 019a4b2c-2000-7000-8000-000000000001 -->

## Overview

Implement the interactive 3-screen planning session lifecycle described in `docs/specs/1-plan-the-day-screen.md`, `2-assign-days-screen.md`, and `3-confirm-plan-screen.md`. Manage the deterministic session state machine (`INIT -> SCREEN_1 -> SCREEN_2 -> SCREEN_3 -> CONFIRMED / CANCELLED`) with stable numbered row indexing. Apply user operations via explicit adjudication, validate constraints, prune suggestions, maintain the immutable decision log, and coordinate atomic persistence via `LocalFileStore`.

## Definition of Done

- [ ] Session state machine transitions cleanly across all 3 screens and validates screen row numbering <!-- id: 019a4b2c-2000-7000-8000-00000000002d -->
- [ ] Explicit user adjudication executes validated operations, logs decisions, and prunes accepted/rejected suggestions <!-- id: 019a4b2c-2000-7000-8000-00000000002e -->
- [ ] Atomic persistence writes modified task/blocker records and the new daily plan to disk via `LocalFileStore` <!-- id: 019a4b2c-2000-7000-8000-00000000002f -->

## Tasks

| # | Task | Status | Assignee | Due Date |
|---|---|---|---|---|
| 12 | [[t1-session-lifecycle-and-screen-mapping\|Session state lifecycle and stable row numbering]] <!-- ref: 019a4b2c-2000-7000-8000-000000000013 --> | [ ] | jordan@example.com | 2026.12.01 |
| 13 | [[t2-adjudication-and-decision-log\|Operation validation, suggestion pruning, and decision log append]] <!-- ref: 019a4b2c-2000-7000-8000-000000000014 --> | [ ] | jordan@example.com | 2026.12.05 |

## Blockers

None

## Status Legend

`[ ]` not started · `[>]` in progress · `[x]` completed · `[-]` cancelled
