---
id: 019a4b2c-1f00-7a10-8000-000000000003
type: task
record_version: 2
title: "Wire Gmail connector behind Communication-Port"
task-state: in-progress
owner: "jordan@example.com"
assignee: "sarah@example.com"
project_id: "019a4b2c-1f00-7a10-8000-000000000001"
milestone_id: "019a4b2c-1f00-7a10-8000-000000000002"
created_at: "2026-10-28T16:40:00Z"
updated_at: "2026-11-03T14:20:05Z"
started_at: "2026-10-30T14:10:00Z"
resolved_at: null
target_date: "2026-11-05"
tags: ["connector", "gmail"]
---
# Wire Gmail connector behind Communication-Port

**Milestone:** [[m2-planning-session-spike|Planning session spike]] <!-- ref: 019a4b2c-1f00-7a10-8000-000000000002 -->

**Project:** [[../project-index|Daily Tasks MCP Server]] <!-- ref: 019a4b2c-1f00-7a10-8000-000000000001 -->

## Requirements

Integrate the Gmail communication port adapter using read-only scopes. The adapter must fetch messages since the last stored cursor timestamp, convert messages to canonical `message.json` formats, and download any attachments to the local spool.

- Read-only OAuth scope enforcement (`gmail.readonly` only).
- Resilient polling with exponential backoff on rate limits.
- Cursor update persistence after every successful batch fetch.

## Definition of Done

- [x] Fetches messages since cursor timestamp <!-- id: 019a4b2c-1f00-7a10-8000-0000000000d3 -->
- [x] Read-only scopes enforced with no write/draft permissions <!-- id: 019a4b2c-1f00-7a10-8000-0000000000d4 -->
- [ ] Unit tests verify email parsing and error handling for dropped connections <!-- id: 019a4b2c-1f00-7a10-8000-0000000000d5 -->

## Inputs

- [[inputs/google-oauth-spec.pdf|Google OAuth Specification]] — Protocol requirements and approved scopes.
- Context & Repository hints:
  - Repo Remote: `https://github.com/NyssaAI/daily-tasks.git` (or `git@github.com:NyssaAI/daily-tasks.git`)
  - Local Clone: `D:/repos/NyssaAI/daily-tasks`
  - Base Branch: `main`
  - Feature Branch: `feat/comms-gmail-adapter`

## Work Product

- Repository PR: https://github.com/NyssaAI/daily-tasks/pull/14
- Delivered code files:
  - Implementation: `src/daily_tasks/sources/gmail.py`
  - Tests: `tests/sources/test_gmail_connector.py`
  - Dependencies: `pyproject.toml` (added `langchain-google-community[gmail]`)

## Result

Pending completion of read-only scope verification and end-to-end integration tests.

## Depends on

None

## Required by

- [[t2-background-fetch-survives-turns|Background fetch survives turns]] <!-- ref: 019a4b2c-1f00-7a10-8000-000000000004 -->

## Blocked by

- [[../blockers/b1-google-oauth-app-verification|Google OAuth app verification]] <!-- ref: 019a4b2c-1f00-7a10-8000-000000000005 -->
