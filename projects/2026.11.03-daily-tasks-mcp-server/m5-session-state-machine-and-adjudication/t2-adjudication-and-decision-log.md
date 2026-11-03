---
id: 019a4b2c-2000-7000-8000-000000000014
type: task
record_version: 2
title: "Operation validation, suggestion pruning, and decision log append"
task-state: completed
owner: "jordan@example.com"
assignee: "jordan@example.com"
project_id: "019a4b2c-2000-7000-8000-000000000001"
milestone_id: "019a4b2c-2000-7000-8000-000000000006"
created_at: "2026-11-03T11:30:00Z"
updated_at: "2026-11-03T11:30:00Z"
started_at: null
resolved_at: null
target_date: "2026-12-05"
tags: ["adjudication", "operations", "decision-log", "atomic-write"]
---
# Operation validation, suggestion pruning, and decision log append

**Milestone:** [[m5-session-state-machine-and-adjudication|Session State Machine & Adjudication]] <!-- ref: 019a4b2c-2000-7000-8000-000000000006 -->

**Project:** [[../project-index|Daily Tasks Python MCP Server]] <!-- ref: 019a4b2c-2000-7000-8000-000000000001 -->

## Requirements

Implement the operation execution engine and the immutable decision log:
1. Validate incoming operations (`select_task`, `unselect_task`, `check_dod_item`, `resolve_blocker`, `accept_suggestion`, `reject_suggestion`, `add_candidate`, `reorder_task`).
2. When a suggestion is accepted or rejected, immediately prune it from pending suggestions and record the rationale.
3. Append every user decision to `decision-log.json` with timestamp, operation, and affected entity references.
4. On `confirm_plan`, stage validated record changes and invoke `LocalFileStore` to write updated files atomically.
5. Strict rule: Never commit changes without explicit user adjudication.

## Definition of Done

- [x] All 8 operations in `docs/specs/operations.json` execute and update session state correctly <!-- id: 019a4b2c-2000-7000-8000-000000000033 -->
- [x] Accepted and rejected suggestions are pruned from suggestions pool and recorded in decision log <!-- id: 019a4b2c-2000-7000-8000-000000000034 -->
- [x] `confirm_plan` commits all record changes and writes the daily plan atomically via `LocalFileStore` <!-- id: 019a4b2c-2000-7000-8000-000000000035 -->

## Inputs

- `src/daily_tasks/session/lifecycle.py`.
- Surgical writer and daily plan generator from Milestone 2.
- `docs/specs/decision-log.json`, `docs/specs/operations.json`.

## Work Product

- Python files: `src/daily_tasks/session/adjudication.py`, `src/daily_tasks/session/decision_logger.py`, `src/daily_tasks/storage/local_file_store.py`.
- Unit tests: `tests/session/test_adjudication.py`, `tests/storage/test_local_file_store.py`.

## Depends on

- [[t1-session-lifecycle-and-screen-mapping|Session state lifecycle and stable row numbering]] <!-- ref: 019a4b2c-2000-7000-8000-000000000013 -->
- [[../m2-markdown-storage-and-cst-engine/t2-surgical-markdown-writer|Surgical CST writer and DoD checkbox toggling]] <!-- ref: 019a4b2c-2000-7000-8000-00000000000c -->
- [[../m2-markdown-storage-and-cst-engine/t3-daily-plan-generator|Daily plan Markdown generator and template parity]] <!-- ref: 019a4b2c-2000-7000-8000-00000000000d -->

## Required by

- [[../m6-mcp-server-and-packaging/t1-mcp-tools-exposition|MCP tool protocols exposition and stdio JSON-RPC transport]] <!-- ref: 019a4b2c-2000-7000-8000-000000000015 -->

## Blocked by

None
