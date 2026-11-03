---
id: 019a4b2c-2000-7000-8000-000000000009
type: task
record_version: 2
title: "Core entity and daily plan DTO models"
task-state: completed
owner: "jordan@example.com"
assignee: "jordan@example.com"
project_id: "019a4b2c-2000-7000-8000-000000000001"
milestone_id: "019a4b2c-2000-7000-8000-000000000002"
created_at: "2026-11-03T11:30:00Z"
updated_at: "2026-11-03T11:30:00Z"
started_at: null
resolved_at: "2026-11-03T12:22:00Z"
target_date: "2026-11-06"
tags: ["pydantic", "dto", "entities", "daily-plan"]
---
# Core entity and daily plan DTO models

**Milestone:** [[m1-dto-models-and-validation|Domain DTO Models & Schema Validation]] <!-- ref: 019a4b2c-2000-7000-8000-000000000002 -->

**Project:** [[../project-index|Daily Tasks Python MCP Server]] <!-- ref: 019a4b2c-2000-7000-8000-000000000001 -->

## Requirements

Implement Pydantic v2 models representing the core domain entities: `Project`, `Milestone`, `Task`, `Blocker`, `DoDItem`, and `DailyPlan` (with `DailyPlanEntry`, `BlockerRef`, and `DecisionRef`). Enforce strict RFC 8259 compliance, ISO 8601 UTC timestamp parsing, and UUIDv7 validation.

## Definition of Done

- [x] Pydantic models defined for `Project`, `Milestone`, `Task`, `Blocker`, and `DailyPlan` <!-- id: 019a4b2c-2000-7000-8000-000000000007 -->
- [x] Roundtrip tests serialize and deserialize `docs/specs/project.json`, `milestone.json`, `task.json`, `blocker.json`, and `daily-plan.json` <!-- id: 019a4b2c-2000-7000-8000-000000000008 -->

## Inputs

- `docs/specs/project.json`
- `docs/specs/milestone.json`
- `docs/specs/task.json`
- `docs/specs/blocker.json`
- `docs/specs/daily-plan.json`

## Work Product

- Implementation: `src/daily_tasks/domain/entities.py`, `src/daily_tasks/domain/daily_plan.py`
- Tests: `tests/domain/test_entity_dtos.py`

## Depends on

- [[t1-project-setup-and-pyproject|Project setup, pyproject.toml and library dependencies]] <!-- ref: 019a4b2c-2000-7000-8000-000000000008 -->

## Required by

- [[t3-communications-and-graph-dtos|Communication, graph, and session DTO models]] <!-- ref: 019a4b2c-2000-7000-8000-00000000000a -->

## Blocked by

None
