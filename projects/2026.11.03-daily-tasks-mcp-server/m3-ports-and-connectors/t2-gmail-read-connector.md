---
id: 019a4b2c-2000-7000-8000-00000000000f
type: task
record_version: 2
title: "Read-only Gmail connector using LangChain tool and Google API"
task-state: not-started
owner: "sarah@example.com"
assignee: "sarah@example.com"
project_id: "019a4b2c-2000-7000-8000-000000000001"
milestone_id: "019a4b2c-2000-7000-8000-000000000004"
created_at: "2026-11-03T11:30:00Z"
updated_at: "2026-11-03T12:55:00Z"
started_at: null
resolved_at: null
target_date: "2026-11-20"
tags: ["gmail", "connector", "langchain", "oauth"]
---
# Read-only Gmail connector using LangChain tool and Google API

**Milestone:** [[m3-ports-and-connectors|Pluggable Ports & Communication Adapters]] <!-- ref: 019a4b2c-2000-7000-8000-000000000004 -->

**Project:** [[../project-index|Daily Tasks Python MCP Server]] <!-- ref: 019a4b2c-2000-7000-8000-000000000001 -->

## Requirements

Implement the read-only Gmail adapter satisfying the `CommunicationPort` protocol using LangChain tool wrappers / Google API client:
1. Enforce strict read-only scope (`https://www.googleapis.com/auth/gmail.readonly`).
2. Resolve access tokens dynamically through `nyssa_ai_configuration.OAuthTokenProvider` held in memory; never read unencrypted token files from disk.
3. Query messages matching `after:{epoch_seconds}` based on `FetchCursors.sources["gmail"].last_timestamp_utc`.
4. Normalize fetched emails into canonical `Message` DTOs (`channel: email`, RFC 8259 strings, sender address, subject, body snippet, thread ID).
5. Operate deterministically with zero runtime LLM calls and zero LLM API key dependencies.

## Definition of Done

- [ ] Adapter authenticates with in-memory token provider and queries message lists <!-- id: 019a4b2c-2000-7000-8000-00000000001e -->
- [ ] Email headers and bodies are mapped to `Message` DTOs conforming to `docs/specs/message.json` <!-- id: 019a4b2c-2000-7000-8000-00000000001f -->
- [ ] Mock integration tests verify incremental fetch updates watermark without duplicates <!-- id: 019a4b2c-2000-7000-8000-000000000020 -->

## Inputs

- `OAuthTokenProvider` providing sealed in-memory Google API credentials.
- `docs/specs/message.json` and `docs/specs/fetch-cursors.json`.

## Work Product

- Python files: `src/daily_tasks/adapters/communication/gmail_connector.py`.
- Unit tests: `test/unit/daily_tasks/adapters/test_gmail_connector.py`.

## Depends on

- [[t1-port-protocols-and-file-sources|Port protocol definitions and Markdown file sources]] <!-- ref: 019a4b2c-2000-7000-8000-00000000000e -->
- [[t4-gmail-oauth-flow|Gmail OAuth 2.0 authorization flow and token management]] <!-- ref: 019a4b2c-2000-7000-8000-000000000018 -->

## Required by

- [[../m4-prematching-and-message-graph/t2-deterministic-message-matcher|Deterministic message correlation and signal word filtering]] <!-- ref: 019a4b2c-2000-7000-8000-000000000012 -->

## Blocked by

- [[../blockers/b1-gmail-oauth-credentials-provisioning|Gmail read-only OAuth credentials provisioning]] <!-- ref: 019a4b2c-2000-7000-8000-000000000017 -->
