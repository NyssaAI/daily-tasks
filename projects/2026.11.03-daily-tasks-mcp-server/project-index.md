---
id: 019a4b2c-2000-7000-8000-000000000001
type: project
record_version: 2
title: "Daily Tasks Python MCP Server"
project-state: in-progress
owner: "jordan@example.com"
created_at: "2026-11-03T11:30:00Z"
updated_at: "2026-11-03T11:30:00Z"
started_at: "2026-11-03T11:30:00Z"
resolved_at: null
target_date: "2026-12-15"
tags: ["mcp", "python", "planning", "deterministic", "tessl"]
---
# Daily Tasks Python MCP Server

**Owner:** jordan@example.com · **Target Date:** 2026-12-15 · **Status:** [>] In Progress  

Deterministic Python Model Context Protocol (MCP) server for the Daily Tasks planning session workflow. Implements pluggable read-only ports (`ProjectPlanPort`, `DailyPlanPort`, `CommunicationPort`), deterministic pre-matching over email/chat messages, in-memory state graph compilation, and validated, atomic writes via `LocalFileStore` exclusively following explicit user adjudication. Integrates `nyssa-ai-logging`, `nyssa-ai-configuration`, and `nyssa-ai-result`.

## [ ] M1: Domain DTO Models & Schema Validation · 2026-11-08 <!-- ref: 019a4b2c-2000-7000-8000-000000000002 -->

| # | Task | Status | Assignee | Due Date |
|---|---|---|---|---|
| 1 | [[m1-dto-models-and-validation/t1-project-setup-and-pyproject\|Project setup, pyproject.toml and library dependencies]] <!-- ref: 019a4b2c-2000-7000-8000-000000000008 --> | [ ] | jordan@example.com | 2026.11.05 |
| 2 | [[m1-dto-models-and-validation/t2-entity-and-plan-dtos\|Core entity and daily plan DTO models]] <!-- ref: 019a4b2c-2000-7000-8000-000000000009 --> | [ ] | jordan@example.com | 2026.11.06 |
| 3 | [[m1-dto-models-and-validation/t3-communications-and-graph-dtos\|Communication, graph, and session DTO models]] <!-- ref: 019a4b2c-2000-7000-8000-00000000000a --> | [ ] | jordan@example.com | 2026.11.08 |

## [ ] M2: Markdown Storage & CST Engine · 2026-11-15 <!-- ref: 019a4b2c-2000-7000-8000-000000000003 -->

| # | Task | Status | Assignee | Due Date |
|---|---|---|---|---|
| 4 | [[m2-markdown-storage-and-cst-engine/t1-frontmatter-and-checklist-parser\|Scalar frontmatter, checklist ID, and wiki-link parser]] <!-- ref: 019a4b2c-2000-7000-8000-00000000000b --> | [ ] | jordan@example.com | 2026.11.11 |
| 5 | [[m2-markdown-storage-and-cst-engine/t2-surgical-markdown-writer\|Surgical CST writer and DoD checkbox toggling]] <!-- ref: 019a4b2c-2000-7000-8000-00000000000c --> | [ ] | jordan@example.com | 2026.11.13 |
| 6 | [[m2-markdown-storage-and-cst-engine/t3-daily-plan-generator\|Daily plan Markdown generator and template parity]] <!-- ref: 019a4b2c-2000-7000-8000-00000000000d --> | [ ] | jordan@example.com | 2026.11.15 |

## [ ] M3: Pluggable Ports & Communication Adapters · 2026-11-22 <!-- ref: 019a4b2c-2000-7000-8000-000000000004 -->

| # | Task | Status | Assignee | Due Date |
|---|---|---|---|---|
| 7 | [[m3-ports-and-connectors/t1-port-protocols-and-file-sources\|Port protocol definitions and Markdown file sources]] <!-- ref: 019a4b2c-2000-7000-8000-00000000000e --> | [ ] | jordan@example.com | 2026.11.18 |
| 8 | [[m3-ports-and-connectors/t4-gmail-oauth-flow\|Gmail OAuth 2.0 authorization flow and token management]] <!-- ref: 019a4b2c-2000-7000-8000-000000000018 --> | [ ] | sarah@example.com | 2026.11.19 |
| 9 | [[m3-ports-and-connectors/t2-gmail-read-connector\|Read-only Gmail connector using LangChain tool and Google API]] <!-- ref: 019a4b2c-2000-7000-8000-00000000000f --> | [ ] | sarah@example.com | 2026.11.20 |
| 10 | [[m3-ports-and-connectors/t3-slack-read-connector-and-cursors\|Read-only Slack connector and cursor persistence]] <!-- ref: 019a4b2c-2000-7000-8000-000000000010 --> | [ ] | alex@example.com | 2026.11.22 |

## [ ] M4: Deterministic Pre-Matching & Message Graph · 2026-11-28 <!-- ref: 019a4b2c-2000-7000-8000-000000000005 -->

| # | Task | Status | Assignee | Due Date |
|---|---|---|---|---|
| 11 | [[m4-prematching-and-message-graph/t1-state-graph-builder\|In-memory StateGraph compilation and derived metrics]] <!-- ref: 019a4b2c-2000-7000-8000-000000000011 --> | [ ] | jordan@example.com | 2026.11.25 |
| 12 | [[m4-prematching-and-message-graph/t2-deterministic-message-matcher\|Deterministic message correlation and signal word filtering]] <!-- ref: 019a4b2c-2000-7000-8000-000000000012 --> | [ ] | jordan@example.com | 2026.11.28 |

## [ ] M5: Session State Machine & Adjudication · 2026-12-05 <!-- ref: 019a4b2c-2000-7000-8000-000000000006 -->

| # | Task | Status | Assignee | Due Date |
|---|---|---|---|---|
| 13 | [[m5-session-state-machine-and-adjudication/t1-session-lifecycle-and-screen-mapping\|Session state lifecycle and stable row numbering]] <!-- ref: 019a4b2c-2000-7000-8000-000000000013 --> | [ ] | jordan@example.com | 2026.12.01 |
| 14 | [[m5-session-state-machine-and-adjudication/t2-adjudication-and-decision-log\|Operation validation, suggestion pruning, and decision log append]] <!-- ref: 019a4b2c-2000-7000-8000-000000000014 --> | [ ] | jordan@example.com | 2026.12.05 |

## [ ] M6: MCP Stdio Server & Packaging · 2026-12-15 <!-- ref: 019a4b2c-2000-7000-8000-000000000007 -->

| # | Task | Status | Assignee | Due Date |
|---|---|---|---|---|
| 15 | [[m6-mcp-server-and-packaging/t1-mcp-tools-exposition\|MCP tool protocols exposition and stdio JSON-RPC transport]] <!-- ref: 019a4b2c-2000-7000-8000-000000000015 --> | [ ] | jordan@example.com | 2026.12.10 |
| 16 | [[m6-mcp-server-and-packaging/t2-logging-and-tessl-syndication\|Structured logging, end-to-end integration tests, and Tessl syndication]] <!-- ref: 019a4b2c-2000-7000-8000-000000000016 --> | [ ] | jordan@example.com | 2026.12.15 |

## Blockers

| # | Status | Blocker | Blocks | Owner |
|---|---|---|---|---|
| B1 | [ ] | [[blockers/b1-gmail-oauth-credentials-provisioning\|Gmail read-only OAuth credentials provisioning]] <!-- ref: 019a4b2c-2000-7000-8000-000000000017 --> | #8, #9 | jordan@example.com |

## Status Legend

`[ ]` not started · `[>]` in progress · `[x]` completed · `[-]` cancelled

## Context & Repository

- Repo Remote: `https://github.com/NyssaAI/daily-tasks.git`
- Local Clone: `D:/repos/NyssaAI/daily-tasks`
- Primary Branch: `main`
- Specifications: `docs/specs/`
- Architecture: `docs/PLANNING_SESSION_CONCEPT.md`
