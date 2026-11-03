---
id: 019a4b2c-2000-7000-8000-000000000010
type: task
record_version: 2
title: "Read-only Slack connector and cursor persistence"
task-state: completed
owner: "alex@example.com"
assignee: "alex@example.com"
project_id: "019a4b2c-2000-7000-8000-000000000001"
milestone_id: "019a4b2c-2000-7000-8000-000000000004"
created_at: "2026-11-03T11:30:00Z"
updated_at: "2026-11-03T12:55:00Z"
started_at: null
resolved_at: null
target_date: "2026-11-22"
tags: ["slack", "connector", "cursors", "communication"]
---
# Read-only Slack connector and cursor persistence

**Milestone:** [[m3-ports-and-connectors|Pluggable Ports & Communication Adapters]] <!-- ref: 019a4b2c-2000-7000-8000-000000000004 -->

**Project:** [[../project-index|Daily Tasks Python MCP Server]] <!-- ref: 019a4b2c-2000-7000-8000-000000000001 -->

## Requirements

Implement the read-only Slack adapter and the persistent cursor manager:
1. Query joined channels and direct mentions using read-only scopes (`channels:history`, `im:history`).
2. Resolve Slack bot/user tokens via `nyssa-ai-configuration` keyring or environment variable (`SLACK_BOT_TOKEN`); never read unencrypted secret files from disk.
3. Map Slack messages to canonical `Message` DTOs (`channel: chat`, sender name/ID, timestamp, text snippet, permalink).
4. Implement `CursorStore` managing `.nyssa-ai/daily-tasks/fetch-cursors.json` to persist last message timestamps across sessions.
5. Support composite `CommunicationPort` multiplexer that queries all configured connectors in parallel and aggregates results.

## Definition of Done

- [x] Slack connector fetches new messages newer than `FetchCursors.sources["slack"].last_timestamp_utc` <!-- id: 019a4b2c-2000-7000-8000-000000000021 -->
- [x] `CursorStore` atomic write guarantees cursor updates are persisted reliably <!-- id: 019a4b2c-2000-7000-8000-000000000022 -->
- [x] Multiplexed `CommunicationPort` handles partial failures gracefully using `nyssa-ai-result` <!-- id: 019a4b2c-2000-7000-8000-000000000023 -->

## Inputs

- Slack Bot / User OAuth token (read-only) resolved via `nyssa-ai-configuration` keyring or environment variable.
- `docs/specs/fetch-cursors.json`.

## Work Product

- Python files: `src/daily_tasks/adapters/communication/slack_connector.py`, `src/daily_tasks/storage/cursors.py`.
- Unit tests: `test/unit/daily_tasks/adapters/test_slack_connector.py`, `test/unit/daily_tasks/storage/test_cursors.py`.

## Depends on

- [[t1-port-protocols-and-file-sources|Port protocol definitions and Markdown file sources]] <!-- ref: 019a4b2c-2000-7000-8000-00000000000e -->

## Required by

- [[../m4-prematching-and-message-graph/t2-deterministic-message-matcher|Deterministic message correlation and signal word filtering]] <!-- ref: 019a4b2c-2000-7000-8000-000000000012 -->

## Blocked by

None
