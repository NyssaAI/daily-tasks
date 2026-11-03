---
id: 019a4b2c-2000-7000-8000-000000000012
type: task
record_version: 2
title: "Deterministic message correlation and signal word filtering"
task-state: not-started
owner: "jordan@example.com"
assignee: "jordan@example.com"
project_id: "019a4b2c-2000-7000-8000-000000000001"
milestone_id: "019a4b2c-2000-7000-8000-000000000005"
created_at: "2026-11-03T11:30:00Z"
updated_at: "2026-11-03T11:30:00Z"
started_at: null
resolved_at: null
target_date: "2026-11-28"
tags: ["matcher", "messages", "deterministic", "regex", "suggestions"]
---
# Deterministic message correlation and signal word filtering

**Milestone:** [[m4-prematching-and-message-graph|Deterministic Pre-Matching & Message Graph]] <!-- ref: 019a4b2c-2000-7000-8000-000000000005 -->

**Project:** [[../project-index|Daily Tasks Python MCP Server]] <!-- ref: 019a4b2c-2000-7000-8000-000000000001 -->

## Requirements

Implement the deterministic message matcher that connects incoming emails and chat messages to existing entities:
1. Exact ID matching: Look for UUIDv7 strings or markdown wiki-links referencing entity titles.
2. Title & Token matching: Normalized substring matching against task titles and blocker descriptions.
3. Signal word extraction: Match status phrases ("done", "completed", "unblocked", "merged", "blocked", "stuck") to infer suggested operations (`check_dod_item`, `resolve_blocker`, `mark_task_done`).
4. Output `message-graph.json` and generate draft `suggestions.json` with confidence scores and reasoning explanations.
5. Strict adherence to rules: Zero runtime LLM calls, zero implicit acceptance.

## Definition of Done

- [ ] Deterministic pattern engine matches incoming messages to active tasks/blockers <!-- id: 019a4b2c-2000-7000-8000-00000000002a -->
- [ ] Generates `MessageGraph` and `Suggestions` matching `message-graph.json` and `suggestions.json` <!-- id: 019a4b2c-2000-7000-8000-00000000002b -->
- [ ] Unit tests pass over diverse email/chat snippets verifying deterministic classification <!-- id: 019a4b2c-2000-7000-8000-00000000002c -->

## Inputs

- Messages from `m3-ports-and-connectors` (or mock datasets).
- `StateGraph` from `t1-state-graph-builder`.
- `docs/specs/message-graph.json` and `docs/specs/suggestions.json`.

## Work Product

- Python files: `src/daily_tasks/matching/message_matcher.py`, `src/daily_tasks/matching/signals.py`, `src/daily_tasks/matching/suggestion_generator.py`.
- Unit tests: `tests/matching/test_message_matcher.py`.

## Depends on

- [[t1-state-graph-builder|In-memory StateGraph compilation and derived metrics]] <!-- ref: 019a4b2c-2000-7000-8000-000000000011 -->
- [[../m3-ports-and-connectors/t2-gmail-read-connector|Read-only Gmail connector using LangChain tool and Google API]] <!-- ref: 019a4b2c-2000-7000-8000-00000000000f -->
- [[../m3-ports-and-connectors/t3-slack-read-connector-and-cursors|Read-only Slack connector and cursor persistence]] <!-- ref: 019a4b2c-2000-7000-8000-000000000010 -->

## Required by

- [[../m5-session-state-machine-and-adjudication/t1-session-lifecycle-and-screen-mapping|Session state lifecycle and stable row numbering]] <!-- ref: 019a4b2c-2000-7000-8000-000000000013 -->

## Blocked by

None
