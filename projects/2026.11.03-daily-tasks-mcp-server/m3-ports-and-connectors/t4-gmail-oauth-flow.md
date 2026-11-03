---
id: 019a4b2c-2000-7000-8000-000000000018
type: task
record_version: 2
title: "Gmail OAuth 2.0 authorization flow and token management"
task-state: completed
owner: "sarah@example.com"
assignee: "sarah@example.com"
project_id: "019a4b2c-2000-7000-8000-000000000001"
milestone_id: "019a4b2c-2000-7000-8000-000000000004"
created_at: "2026-11-03T11:30:00Z"
updated_at: "2026-11-03T12:55:00Z"
started_at: null
resolved_at: null
target_date: "2026-11-19"
tags: ["gmail", "oauth", "auth", "security", "tokens"]
---
# Gmail OAuth 2.0 authorization flow and token management

**Milestone:** [[m3-ports-and-connectors|Pluggable Ports & Communication Adapters]] <!-- ref: 019a4b2c-2000-7000-8000-000000000004 -->

**Project:** [[../project-index|Daily Tasks Python MCP Server]] <!-- ref: 019a4b2c-2000-7000-8000-000000000001 -->

## Requirements

Implement the interactive first-run OAuth 2.0 authorization flow and token lifecycle for the Gmail communication adapter using `nyssa-ai-configuration`:
1. Use `nyssa_ai_configuration.OAuthFlowClient` to execute the PKCE loopback authorization flow and exchange authorization codes for refresh and access tokens enforcing read-only scope (`https://www.googleapis.com/auth/gmail.readonly`).
2. Manage and seal token grants in memory using `nyssa_ai_configuration.OAuthTokenProvider` backed by `KeyringDefault` (OS credential store) or `KeyringInMemory`. Tokens and secrets must never be saved as unencrypted files on disk.
3. Automatically refresh expiring access tokens headlessly under lock so planning sessions execute without user intervention.
4. Mask secrets and tokens from `repr()`, debug prints, and logging outputs to prevent credential leakage.
5. Provide a CLI helper command `python -m daily_tasks.auth.gmail` and an MCP server helper to trigger first-run authorization when tokens are absent.

## Definition of Done

- [x] `OAuthFlowClient` handles Google OAuth 2.0 PKCE callback and token exchange <!-- id: 019a4b2c-2000-7000-8000-00000000103f -->
- [x] `OAuthTokenProvider` securely retains token grants in memory/keyring and refreshes expired tokens headlessly without plain-text disk writes <!-- id: 019a4b2c-2000-7000-8000-000000001040 -->
- [x] Automated tests using mock OAuth endpoints verify token exchange and refresh flows <!-- id: 019a4b2c-2000-7000-8000-000000001041 -->

## Inputs

- Google Cloud Console OAuth 2.0 client credentials (`client_id`, `client_secret`) resolved via `nyssa-ai-configuration`.
- `docs/specs/port-config.json`.

## Work Product

- Python files: `src/daily_tasks/adapters/communication/gmail_oauth.py`.
- Unit tests: `test/unit/daily_tasks/adapters/test_gmail_oauth.py`.

## Depends on

- [[t1-port-protocols-and-file-sources|Port protocol definitions and Markdown file sources]] <!-- ref: 019a4b2c-2000-7000-8000-00000000000e -->

## Required by

- [[t2-gmail-read-connector|Read-only Gmail connector using LangChain tool and Google API]] <!-- ref: 019a4b2c-2000-7000-8000-00000000000f -->

## Blocked by

- [[../blockers/b1-gmail-oauth-credentials-provisioning|Gmail read-only OAuth credentials provisioning]] <!-- ref: 019a4b2c-2000-7000-8000-000000000017 -->
