---
id: 019a4b2c-2000-7000-8000-000000000005
type: milestone
record_version: 2
title: "Deterministic Pre-Matching & Message Graph"
milestone-state: not-started
project_id: "019a4b2c-2000-7000-8000-000000000001"
created_at: "2026-11-03T11:30:00Z"
updated_at: "2026-11-03T11:30:00Z"
started_at: null
resolved_at: null
target_date: "2026-11-28"
tags: ["state-graph", "pre-matching", "deterministic", "regex", "correlations"]
---
# [ ] M4: Deterministic Pre-Matching & Message Graph · 2026-11-28

**Project:** [[../project-index|Daily Tasks Python MCP Server]] <!-- ref: 019a4b2c-2000-7000-8000-000000000001 -->

## Overview

Build the core deterministic intelligence layer of the Daily Tasks server. Synthesizes loaded project entities into an in-memory `StateGraph` calculating completion metrics, DoD progress ratios, and dependency trees. Correlates newly fetched communications with tasks and blockers using strict deterministic rules (UUID matching, title substring matching, signal word classification like "done", "blocked", "merged", and assignee thread matching) with zero LLM API calls. Produces `message-graph.json` and suggested operations.

## Definition of Done

- [ ] `StateGraphBuilder` compiles project entities into a linked graph matching `docs/specs/state-graph.json` <!-- id: 019a4b2c-2000-7000-8000-000000000024 -->
- [ ] Deterministic message matcher correlates communications with tasks and blockers with confidence scores <!-- id: 019a4b2c-2000-7000-8000-000000000025 -->
- [ ] Suggestion engine emits candidates in `suggestions.json` schema without time fitting or implicit acceptance <!-- id: 019a4b2c-2000-7000-8000-000000000026 -->

## Tasks

| # | Task | Status | Assignee | Due Date |
|---|---|---|---|---|
| 10 | [[t1-state-graph-builder\|In-memory StateGraph compilation and derived metrics]] <!-- ref: 019a4b2c-2000-7000-8000-000000000011 --> | [ ] | jordan@example.com | 2026.11.25 |
| 11 | [[t2-deterministic-message-matcher\|Deterministic message correlation and signal word filtering]] <!-- ref: 019a4b2c-2000-7000-8000-000000000012 --> | [ ] | jordan@example.com | 2026.11.28 |

## Blockers

None

## Status Legend

`[ ]` not started · `[>]` in progress · `[x]` completed · `[-]` cancelled
