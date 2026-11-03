---
id: 019a4b2c-2000-7000-8000-000000000013
type: task
record_version: 2
title: "Session state lifecycle and stable row numbering"
task-state: not-started
owner: "jordan@example.com"
assignee: "jordan@example.com"
project_id: "019a4b2c-2000-7000-8000-000000000001"
milestone_id: "019a4b2c-2000-7000-8000-000000000006"
created_at: "2026-11-03T11:30:00Z"
updated_at: "2026-11-03T11:30:00Z"
started_at: null
resolved_at: null
target_date: "2026-12-01"
tags: ["session", "screens", "row-mapping", "state-machine"]
---
# Session state lifecycle and stable row numbering

**Milestone:** [[m5-session-state-machine-and-adjudication|Session State Machine & Adjudication]] <!-- ref: 019a4b2c-2000-7000-8000-000000000006 -->

**Project:** [[../project-index|Daily Tasks Python MCP Server]] <!-- ref: 019a4b2c-2000-7000-8000-000000000001 -->

## Requirements

Implement the session lifecycle controller and screen row indexing:
1. Initialize session by loading `StateGraph`, previous daily plan, and new messages.
2. Render Screen 1 (`plan_the_day`): carry-forward items, conditional suggestions, and active blockers with numbered indices.
3. Render Screen 2 (`assign_days`): per-project tasks and blockers for multi-day allocations.
4. Render Screen 3 (`confirm_plan`): final local-day plan recap and numbered reindexing.
5. Maintain bidirectional row mappings (`screen_1_rows`, `screen_2_rows`, `screen_3_rows` in `planning-session.json`) so user prompts can refer unambiguously to `#1`, `#2`, etc.

## Definition of Done

- [ ] Session transitions through all screens and enforces valid state transitions <!-- id: 019a4b2c-2000-7000-8000-000000000030 -->
- [ ] Row mapping tables are populated and resolve integer indices to UUIDv7 entity IDs <!-- id: 019a4b2c-2000-7000-8000-000000000031 -->
- [ ] Session snapshots match the schema specified in `docs/specs/planning-session.json` <!-- id: 019a4b2c-2000-7000-8000-000000000032 -->

## Inputs

- `docs/specs/1-plan-the-day-screen.md`, `2-assign-days-screen.md`, `3-confirm-plan-screen.md`.
- `StateGraph` from Milestone 4.

## Work Product

- Python files: `src/daily_tasks/session/lifecycle.py`, `src/daily_tasks/session/screen_renderer.py`.
- Unit tests: `tests/session/test_session_lifecycle.py`.

## Depends on

- [[../m4-prematching-and-message-graph/t1-state-graph-builder|In-memory StateGraph compilation and derived metrics]] <!-- ref: 019a4b2c-2000-7000-8000-000000000011 -->
- [[../m4-prematching-and-message-graph/t2-deterministic-message-matcher|Deterministic message correlation and signal word filtering]] <!-- ref: 019a4b2c-2000-7000-8000-000000000012 -->

## Required by

- [[t2-adjudication-and-decision-log|Operation validation, suggestion pruning, and decision log append]] <!-- ref: 019a4b2c-2000-7000-8000-000000000014 -->

## Blocked by

None
