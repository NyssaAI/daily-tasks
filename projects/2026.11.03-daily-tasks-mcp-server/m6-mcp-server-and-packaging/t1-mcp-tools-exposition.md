---
id: 019a4b2c-2000-7000-8000-000000000015
type: task
record_version: 2
title: "MCP tool protocols exposition and stdio JSON-RPC transport"
task-state: not-started
owner: "jordan@example.com"
assignee: "jordan@example.com"
project_id: "019a4b2c-2000-7000-8000-000000000001"
milestone_id: "019a4b2c-2000-7000-8000-000000000007"
created_at: "2026-11-03T11:30:00Z"
updated_at: "2026-11-03T11:30:00Z"
started_at: null
resolved_at: null
target_date: "2026-12-10"
tags: ["mcp", "tools", "stdio", "json-rpc"]
---
# MCP tool protocols exposition and stdio JSON-RPC transport

**Milestone:** [[m6-mcp-server-and-packaging|MCP Stdio Server & Packaging]] <!-- ref: 019a4b2c-2000-7000-8000-000000000007 -->

**Project:** [[../project-index|Daily Tasks Python MCP Server]] <!-- ref: 019a4b2c-2000-7000-8000-000000000001 -->

## Requirements

Implement the MCP standard stdio protocol server exposing the planning tools:
1. `daily_tasks_start_session(date: str | None = None)`: Initializes session, parses markdown store, ingests unread communications, generates suggestions, returns Screen 1.
2. `daily_tasks_execute_operations(operations: list[Operation])`: Executes user operations (selection, checkbox toggle, blocker resolution, suggestion accept/reject), records decisions, returns updated screen.
3. `daily_tasks_advance_screen(target_screen: int)`: Transitions between screens 1, 2, and 3.
4. `daily_tasks_confirm_plan()`: Stages validated changes, writes new `daily-plan.md` and updated record files via `LocalFileStore`, updates fetch cursors, finishes session.
5. `daily_tasks_cancel_session()`: Discards in-memory session without modifying any disk records.

## Definition of Done

- [ ] MCP server implements tools matching `docs/specs/tool-results.json` and stdio transport <!-- id: 019a4b2c-2000-7000-8000-000000000039 -->
- [ ] Stdio communication conforms strictly to MCP JSON-RPC protocol specification <!-- id: 019a4b2c-2000-7000-8000-00000000003a -->
- [ ] Integration tests simulate full MCP client sessions without protocol errors <!-- id: 019a4b2c-2000-7000-8000-00000000003b -->

## Inputs

- `src/daily_tasks/session/lifecycle.py` and `src/daily_tasks/session/adjudication.py`.
- `docs/specs/tool-results.json`.

## Work Product

- Python files: `src/daily_tasks/server/mcp_server.py`, `src/daily_tasks/server/tools.py`.
- Unit tests: `tests/server/test_mcp_server.py`.

## Depends on

- [[../m5-session-state-machine-and-adjudication/t2-adjudication-and-decision-log|Operation validation, suggestion pruning, and decision log append]] <!-- ref: 019a4b2c-2000-7000-8000-000000000014 -->

## Required by

- [[t2-logging-and-tessl-syndication|Structured logging, end-to-end integration tests, and Tessl syndication]] <!-- ref: 019a4b2c-2000-7000-8000-000000000016 -->

## Blocked by

None
