---
id: 019a4b2c-2000-7000-8000-000000000018
type: task
record_version: 2
title: "Gmail OAuth 2.0 authorization flow and token management"
task-state: not-started
owner: "sarah@example.com"
assignee: "sarah@example.com"
project_id: "019a4b2c-2000-7000-8000-000000000001"
milestone_id: "019a4b2c-2000-7000-8000-000000000004"
created_at: "2026-11-03T11:30:00Z"
updated_at: "2026-11-03T11:50:00Z"
started_at: null
resolved_at: null
target_date: "2026-11-19"
tags: ["gmail", "oauth", "auth", "security", "tokens"]
---
# Gmail OAuth 2.0 authorization flow and token management

**Milestone:** [[m3-ports-and-connectors|Pluggable Ports & Communication Adapters]] <!-- ref: 019a4b2c-2000-7000-8000-000000000004 -->

**Project:** [[../project-index|Daily Tasks Python MCP Server]] <!-- ref: 019a4b2c-2000-7000-8000-000000000001 -->

## Requirements

Implement the interactive first-run OAuth 2.0 authorization flow and token lifecycle for the Gmail communication adapter:
1. Implement local loopback server (`http://localhost:8080/callback`) to receive the OAuth authorization code from Google's consent screen.
2. Exchange authorization code for refresh and access tokens enforcing read-only scope (`https://www.googleapis.com/auth/gmail.readonly`).
3. Store tokens in `.nyssa-ai/daily-tasks/tokens/gmail.json` with strict file permissions (`0600`).
4. Implement automatic token refresh logic so subsequent planning sessions execute headlessly without user intervention.
5. Provide a CLI command `python -m daily_tasks.auth.gmail` and an MCP server helper to trigger first-run authorization when tokens are absent or expired.

## Definition of Done

- [ ] Loopback redirect server handles Google OAuth 2.0 callback and extracts authorization code <!-- id: 019a4b2c-2000-7000-8000-00000000103f -->
- [ ] Token manager securely saves tokens to `.nyssa-ai/daily-tasks/tokens/gmail.json` and refreshes expired access tokens <!-- id: 019a4b2c-2000-7000-8000-000000001040 -->
- [ ] Automated tests using mock OAuth endpoints verify token exchange and refresh flows <!-- id: 019a4b2c-2000-7000-8000-000000001041 -->

## Inputs

- Google Cloud Console OAuth 2.0 client credentials (`client_id`, `client_secret`).
- `docs/specs/port-config.json`.

## Work Product

- Python files: `src/daily_tasks/auth/gmail_oauth.py`, `src/daily_tasks/auth/token_store.py`.
- Unit tests: `tests/auth/test_gmail_oauth.py`.

## Depends on

- [[t1-port-protocols-and-file-sources|Port protocol definitions and Markdown file sources]] <!-- ref: 019a4b2c-2000-7000-8000-00000000000e -->

## Required by

- [[t2-gmail-read-connector|Read-only Gmail connector using LangChain tool and Google API]] <!-- ref: 019a4b2c-2000-7000-8000-00000000000f -->

## Blocked by

- [[../blockers/b1-gmail-oauth-credentials-provisioning|Gmail read-only OAuth credentials provisioning]] <!-- ref: 019a4b2c-2000-7000-8000-000000000017 -->
