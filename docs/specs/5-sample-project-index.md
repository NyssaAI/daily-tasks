---
id: 019a4b2c-1f00-7a10-8000-000000000001
type: project
record_version: 2
title: "Daily Tasks MCP Server"
project-state: in-progress
owner: "jordan@example.com"
created_at: "2026-10-20T10:00:00Z"
updated_at: "2026-11-02T19:00:00Z"
started_at: "2026-10-20T10:30:00Z"
resolved_at: null
target_date: "2026-11-30"
tags: ["mcp", "planning", "automation"]
---
# Daily Tasks MCP Server

**Owner:** jordan@example.com · **Target Date:** 2026-11-30 · **Status:** [>] In Progress  

Python MCP server that runs the plan-the-day session with pluggable ports.

## [x] M1: Design · 2026-10-25 <!-- ref: 019a4b2c-1f00-7a10-8000-000000000010 -->

| # | Task | Status | Assignee | Due Date |
|---|---|---|---|---|
| 1 | [[m1-design/t1-architecture-spike\|Architecture spike and port contracts]] <!-- ref: 019a4b2c-1f00-7a10-8000-000000000030 --> | [x] | jordan@example.com | 2026.10.22 |
| 2 | [[m1-design/t2-dto-schemas\|Define DTO JSON schemas]] <!-- ref: 019a4b2c-1f00-7a10-8000-000000000031 --> | [x] | jordan@example.com | 2026.10.25 |

## [>] M2: Planning session spike · 2026-11-10 <!-- ref: 019a4b2c-1f00-7a10-8000-000000000002 -->

| # | Task | Status | Assignee | Due Date |
|---|---|---|---|---|
| 3 | [[m2-planning-session-spike/t1-wire-gmail-connector\|Wire Gmail connector]] <!-- ref: 019a4b2c-1f00-7a10-8000-000000000003 --> | [>] | sarah@example.com | 2026.11.05 |
| 4 | [[m2-planning-session-spike/t2-background-fetch-survives-turns\|Background fetch survives turns]] <!-- ref: 019a4b2c-1f00-7a10-8000-000000000004 --> | [>] | alex@example.com | — |
| 5 | [[m2-planning-session-spike/t3-draft-connector-readme\|Draft connector README]] <!-- ref: 019a4b2c-1f00-7a10-8000-000000000007 --> | [ ] | — | — |
| 6 | [[m2-planning-session-spike/t4-review-slack-connector-pr\|Review Slack connector PR]] <!-- ref: 019a4b2c-1f00-7a10-8000-000000000008 --> | [ ] | — | 2026.11.05 |

## [>] M3: Connectors · 2026-11-20 <!-- ref: 019a4b2c-1f00-7a10-8000-000000000012 -->

| # | Task | Status | Assignee | Due Date |
|---|---|---|---|---|
| 7 | [[m3-connectors/t1-slack-connector\|Slack connector]] <!-- ref: 019a4b2c-1f00-7a10-8000-000000000014 --> | [>] | jordan@example.com | 2026.11.12 |
| 8 | [[m3-connectors/t2-outlook-connector\|Outlook connector]] <!-- ref: 019a4b2c-1f00-7a10-8000-000000000025 --> | [ ] | — | — |
| 9 | [[m3-connectors/t3-connector-error-reporting\|Connector error reporting]] <!-- ref: 019a4b2c-1f00-7a10-8000-000000000017 --> | [ ] | — | — |

## [ ] M4: Packaging · 2026-11-30 <!-- ref: 019a4b2c-1f00-7a10-8000-000000000021 -->

| # | Task | Status | Assignee | Due Date |
|---|---|---|---|---|
| 10 | [[m4-packaging/t1-mcp-entrypoint\|CLI and stdio MCP entrypoint]] <!-- ref: 019a4b2c-1f00-7a10-8000-000000000032 --> | [ ] | — | 2026.11.28 |
| 11 | [[m4-packaging/t2-plugin-manifest\|Publish plugin manifest]] <!-- ref: 019a4b2c-1f00-7a10-8000-000000000033 --> | [ ] | — | 2026.11.30 |

## Blockers

| # | Status | Blocker | Blocks | Owner |
|---|---|---|---|---|
| B1 | [ ] | [[blockers/b1-google-oauth-app-verification\|Google OAuth app verification]] <!-- ref: 019a4b2c-1f00-7a10-8000-000000000005 --> | #3, #5 | jordan@example.com |

## Status Legend

`[ ]` not started · `[>]` in progress · `[x]` completed · `[-]` cancelled

## Context & Repository

- Repo Remote: `https://github.com/NyssaAI/daily-tasks.git`
- Local Clone: `D:/repos/NyssaAI/daily-tasks`
- Primary Branch: `main`
- Documentation: `docs/PLANNING_SESSION_CONCEPT.md`
