---
id: 019a4b2c-2000-7000-8000-00000000000e
type: task
record_version: 2
title: "Port protocol definitions and Markdown file sources"
task-state: completed
owner: "jordan@example.com"
assignee: "jordan@example.com"
project_id: "019a4b2c-2000-7000-8000-000000000001"
milestone_id: "019a4b2c-2000-7000-8000-000000000004"
created_at: "2026-11-03T11:30:00Z"
updated_at: "2026-11-03T11:30:00Z"
started_at: null
resolved_at: null
target_date: "2026-11-18"
tags: ["ports", "architecture", "protocols", "file-store"]
---
# Port protocol definitions and Markdown file sources

**Milestone:** [[m3-ports-and-connectors|Pluggable Ports & Communication Adapters]] <!-- ref: 019a4b2c-2000-7000-8000-000000000004 -->

**Project:** [[../project-index|Daily Tasks Python MCP Server]] <!-- ref: 019a4b2c-2000-7000-8000-000000000001 -->

## Requirements

Define the abstract runtime ports specified in `docs/PLANNING_SESSION_CONCEPT.md` using Python `typing.Protocol`:
1. `ProjectPlanPort`: Read-only port returning all active `Project`, `Milestone`, `Task`, and `Blocker` records.
2. `DailyPlanPort`: Read-only port returning previous and current `DailyPlan` records.
3. `CommunicationPort`: Read-only port providing `fetch_new_messages(since: FetchCursors) -> tuple[list[Message], FetchCursors]`.
4. `LocalFileStore`: Authorized store applying validated record changes and daily plans exclusively following explicit user adjudication.
5. Implement the file-backed adapters `MarkdownProjectPlanAdapter` and `MarkdownDailyPlanAdapter` powered by the CST parser from M2.

## Definition of Done

- [x] Python protocols created with full type annotations returning `nyssa_ai_result.Result` <!-- id: 019a4b2c-2000-7000-8000-00000000001b -->
- [x] `MarkdownProjectPlanAdapter` discovers projects, milestones, tasks, and blockers recursively in vault path <!-- id: 019a4b2c-2000-7000-8000-00000000001c -->
- [x] `MarkdownDailyPlanAdapter` loads recent daily plans by date key from `plans/` directory <!-- id: 019a4b2c-2000-7000-8000-00000000001d -->

## Inputs

- `docs/PLANNING_SESSION_CONCEPT.md` architecture section.
- `src/daily_tasks/storage/cst/parser.py`.

## Work Product

- Python files: `src/daily_tasks/ports/protocols.py`, `src/daily_tasks/adapters/markdown_project_adapter.py`, `src/daily_tasks/adapters/markdown_daily_plan_adapter.py`.
- Unit tests: `tests/adapters/test_markdown_adapters.py`.

## Depends on

- [[../m2-markdown-storage-and-cst-engine/t1-frontmatter-and-checklist-parser|Scalar frontmatter, checklist ID, and wiki-link parser]] <!-- ref: 019a4b2c-2000-7000-8000-00000000000b -->

## Required by

- [[../m4-prematching-and-message-graph/t1-state-graph-builder|In-memory StateGraph compilation and derived metrics]] <!-- ref: 019a4b2c-2000-7000-8000-000000000011 -->

## Blocked by

None
