---
id: 019a4b2c-2000-7000-8000-00000000000a
type: task
record_version: 2
title: "Communication, graph, and session DTO models"
task-state: completed
owner: "jordan@example.com"
assignee: "jordan@example.com"
project_id: "019a4b2c-2000-7000-8000-000000000001"
milestone_id: "019a4b2c-2000-7000-8000-000000000002"
created_at: "2026-11-03T11:30:00Z"
updated_at: "2026-11-03T11:30:00Z"
started_at: null
resolved_at: "2026-11-03T12:22:00Z"
target_date: "2026-11-08"
tags: ["pydantic", "dto", "messages", "state-graph", "session"]
---
# Communication, graph, and session DTO models

**Milestone:** [[m1-dto-models-and-validation|Domain DTO Models & Schema Validation]] <!-- ref: 019a4b2c-2000-7000-8000-000000000002 -->

**Project:** [[../project-index|Daily Tasks Python MCP Server]] <!-- ref: 019a4b2c-2000-7000-8000-000000000001 -->

## Requirements

Implement Pydantic v2 models representing the remaining schemas:
1. Communications & Cursors: `Message`, `MessageLog`, `MessageGraph`, `FetchCursors`.
2. Session & State Graph: `StateGraph`, `Suggestions`, `DecisionLog`, `DecisionLogEntry`, `Operations` (discriminated union of operations), `RecordChange`, `PlanningSession` (with screen 1, 2, and 3 row mappings), and `ToolResults`.
3. Configuration: `PortConfig`.

Ensure validation tests against `docs/specs/*.json` samples pass without error.

## Definition of Done

- [x] Pydantic models implemented for communication schemas (`message.json`, `fetch-cursors.json`, `message-graph.json`) <!-- id: 019a4b2c-2000-7000-8000-000000000009 -->
- [x] Pydantic models implemented for state graph, session state, suggestions, and operations <!-- id: 019a4b2c-2000-7000-8000-00000000000a -->
- [x] Round-trip validation test suite passes on all 18 JSON files in `docs/specs/` <!-- id: 019a4b2c-2000-7000-8000-00000000000b -->

## Inputs

- `docs/specs/*.json` schemas and canonical examples.
- `t2-entity-and-plan-dtos` base entity models.

## Work Product

- Python files: `src/daily_tasks/domain/messages.py`, `src/daily_tasks/domain/session.py`, `src/daily_tasks/domain/operations.py`.
- Unit tests: `tests/domain/test_communication_dtos.py`, `tests/domain/test_session_dtos.py`.

## Depends on

- [[t2-entity-and-plan-dtos|Core entity and daily plan DTO models]] <!-- ref: 019a4b2c-2000-7000-8000-000000000009 -->

## Required by

- [[../m2-markdown-storage-and-cst-engine/t1-frontmatter-and-checklist-parser|Scalar frontmatter, checklist ID, and wiki-link parser]] <!-- ref: 019a4b2c-2000-7000-8000-00000000000b -->
- [[../m4-prematching-and-message-graph/t1-state-graph-builder|In-memory StateGraph compilation and derived metrics]] <!-- ref: 019a4b2c-2000-7000-8000-000000000011 -->

## Blocked by

None
