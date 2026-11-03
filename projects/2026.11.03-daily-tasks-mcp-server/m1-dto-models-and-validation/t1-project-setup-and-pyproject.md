---
id: 019a4b2c-2000-7000-8000-000000000008
type: task
record_version: 2
title: "Project setup, pyproject.toml and library dependencies"
task-state: completed
owner: "jordan@example.com"
assignee: "jordan@example.com"
project_id: "019a4b2c-2000-7000-8000-000000000001"
milestone_id: "019a4b2c-2000-7000-8000-000000000002"
created_at: "2026-11-03T11:30:00Z"
updated_at: "2026-11-03T11:30:00Z"
started_at: null
resolved_at: "2026-11-03T12:22:00Z"
target_date: "2026-11-05"
tags: ["setup", "python", "pyproject", "dependencies"]
---
# Project setup, pyproject.toml and library dependencies

**Milestone:** [[m1-dto-models-and-validation|Domain DTO Models & Schema Validation]] <!-- ref: 019a4b2c-2000-7000-8000-000000000002 -->

**Project:** [[../project-index|Daily Tasks Python MCP Server]] <!-- ref: 019a4b2c-2000-7000-8000-000000000001 -->

## Requirements

Configure the root `pyproject.toml` file establishing package metadata, Python >=3.12 compatibility, and core dependencies. Ensure `nyssa-ai-logging`, `nyssa-ai-configuration`, `nyssa-ai-result`, `pydantic>=2.10`, and `langchain-core` are declared. Configure `pytest` and `ruff` linting configurations.

## Definition of Done

- [x] `pyproject.toml` created with package build metadata and dependencies <!-- id: 019a4b2c-2000-7000-8000-000000000004 -->
- [x] Source package directory `src/daily_tasks/` created with `__init__.py` <!-- id: 019a4b2c-2000-7000-8000-000000000005 -->
- [x] Pytest runs cleanly via `python -m pytest` <!-- id: 019a4b2c-2000-7000-8000-000000000006 -->

## Inputs

- `AGENTS.md` Python guidelines (Python >=3.12, `src/daily_tasks/`, `pytest`).
- Local environment dependencies: `nyssa-ai-logging`, `nyssa-ai-configuration`, `nyssa-ai-result`.

## Work Product

- Files: `pyproject.toml`, `src/daily_tasks/__init__.py`, `tests/conftest.py`.

## Depends on

None

## Required by

- [[t2-entity-and-plan-dtos|Core entity and daily plan DTO models]] <!-- ref: 019a4b2c-2000-7000-8000-000000000009 -->

## Blocked by

None
