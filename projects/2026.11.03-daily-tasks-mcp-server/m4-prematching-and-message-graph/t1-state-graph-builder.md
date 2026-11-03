---
id: 019a4b2c-2000-7000-8000-000000000011
type: task
record_version: 2
title: "In-memory StateGraph compilation and derived metrics"
task-state: completed
owner: "jordan@example.com"
assignee: "jordan@example.com"
project_id: "019a4b2c-2000-7000-8000-000000000001"
milestone_id: "019a4b2c-2000-7000-8000-000000000005"
created_at: "2026-11-03T11:30:00Z"
updated_at: "2026-11-03T11:30:00Z"
started_at: null
resolved_at: null
target_date: "2026-11-25"
tags: ["state-graph", "compilation", "metrics", "graph"]
---
# In-memory StateGraph compilation and derived metrics

**Milestone:** [[m4-prematching-and-message-graph|Deterministic Pre-Matching & Message Graph]] <!-- ref: 019a4b2c-2000-7000-8000-000000000005 -->

**Project:** [[../project-index|Daily Tasks Python MCP Server]] <!-- ref: 019a4b2c-2000-7000-8000-000000000001 -->

## Requirements

Implement the `StateGraphBuilder` that aggregates models from `ProjectPlanPort` and `DailyPlanPort` into a connected graph:
1. Index projects, milestones, tasks, and blockers by their UUIDv7 identifiers.
2. Calculate derived metrics: DoD completion counts and ratios (e.g. `1/3`), blocker counts, and milestone completion percentages.
3. Construct adjacency maps for bidirectional relationships (task blockers, milestone children, previous day plan carry-forwards).
4. Validate that output conforms to `docs/specs/state-graph.json`.

## Definition of Done

- [x] `StateGraphBuilder` creates an in-memory graph from all parsed project entities <!-- id: 019a4b2c-2000-7000-8000-000000000027 -->
- [x] Accurately computes DoD progress string fractions (`x/total`) and blocker impact sets <!-- id: 019a4b2c-2000-7000-8000-000000000028 -->
- [x] Serializes cleanly to `docs/specs/state-graph.json` structure with 100% schema compliance <!-- id: 019a4b2c-2000-7000-8000-000000000029 -->

## Inputs

- `ProjectPlanPort` and `DailyPlanPort` outputs.
- `docs/specs/state-graph.json`.

## Work Product

- Python files: `src/daily_tasks/graph/state_graph_builder.py`, `src/daily_tasks/graph/models.py`.
- Unit tests: `tests/graph/test_state_graph_builder.py`.

## Depends on

- [[../m1-dto-models-and-validation/t3-communications-and-graph-dtos|Communication, graph, and session DTO models]] <!-- ref: 019a4b2c-2000-7000-8000-00000000000a -->
- [[../m3-ports-and-connectors/t1-port-protocols-and-file-sources|Port protocol definitions and Markdown file sources]] <!-- ref: 019a4b2c-2000-7000-8000-00000000000e -->

## Required by

- [[t2-deterministic-message-matcher|Deterministic message correlation and signal word filtering]] <!-- ref: 019a4b2c-2000-7000-8000-000000000012 -->
- [[../m5-session-state-machine-and-adjudication/t1-session-lifecycle-and-screen-mapping|Session state lifecycle and stable row numbering]] <!-- ref: 019a4b2c-2000-7000-8000-000000000013 -->

## Blocked by

None
