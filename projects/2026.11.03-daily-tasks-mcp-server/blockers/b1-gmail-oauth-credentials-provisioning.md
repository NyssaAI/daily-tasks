---
id: 019a4b2c-2000-7000-8000-000000000017
type: blocker
record_version: 2
title: "Gmail read-only OAuth credentials provisioning"
blocker-state: open
impact: high
project_id: "019a4b2c-2000-7000-8000-000000000001"
created_at: "2026-11-03T11:30:00Z"
updated_at: "2026-11-03T11:30:00Z"
resolved_at: null
target_date: "2026-11-10"
tags: ["oauth", "gmail", "credentials", "external"]
---
# B1 — Gmail read-only OAuth credentials provisioning

**Project:** [[../project-index|Daily Tasks Python MCP Server]] <!-- ref: 019a4b2c-2000-7000-8000-000000000001 -->

## Impact & Summary

Google Cloud Console OAuth 2.0 Client ID credentials with `gmail.readonly` scope are required to run integration tests and live message fetching for the Gmail connector. Until provisioned, local execution must rely on mock message fixtures.

## Resolved When

- Google Cloud project OAuth consent screen configured for internal testing.
- Client secret and refresh token provisioned in local test environment configuration (`.env` / configuration port).
- Integration test successfully authenticates and fetches message thread list without interactive login prompt.

## Blocks

- [[../m3-ports-and-connectors/t4-gmail-oauth-flow|Gmail OAuth 2.0 authorization flow and token management]] <!-- ref: 019a4b2c-2000-7000-8000-000000000018 -->
- [[../m3-ports-and-connectors/t2-gmail-read-connector|Read-only Gmail connector using LangChain tool and Google API]] <!-- ref: 019a4b2c-2000-7000-8000-00000000000f -->
- [[../m3-ports-and-connectors/m3-ports-and-connectors|Pluggable Ports & Communication Adapters]] <!-- ref: 019a4b2c-2000-7000-8000-000000000004 -->

## External References

- Google Workspace API Console: `https://console.cloud.google.com/apis/credentials`
- Gmail API Scopes Reference: `https://developers.google.com/gmail/api/auth/scopes`
