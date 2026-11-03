---
id: 019a4b2c-2000-7000-8000-000000000017
type: blocker
record_version: 2
title: "Gmail read-only OAuth credentials provisioning"
state: active
owner: "jordan@example.com"
project_id: "019a4b2c-2000-7000-8000-000000000001"
created_at: "2026-11-03T11:30:00Z"
updated_at: "2026-11-03T12:55:00Z"
resolved_at: null
impact: critical
source: external
resolved_when: "Google Cloud Console OAuth 2.0 Client ID and secret are provisioned and stored in the secure keyring via nyssa-ai-configuration."
blocks:
  - "019a4b2c-2000-7000-8000-000000000018"
  - "019a4b2c-2000-7000-8000-00000000000f"
tags: ["oauth", "gmail", "credentials", "external"]
---
# B1 - Gmail read-only OAuth credentials provisioning

**Project:** [[../project-index|Daily Tasks Python MCP Server]] <!-- ref: 019a4b2c-2000-7000-8000-000000000001 -->

## Impact

Critical path blocker for Milestone 3 (Pluggable Ports & Communication Adapters). Prevents live integration testing of the read-only Gmail communication connector.

## Description

Google Cloud Console OAuth 2.0 Client ID credentials with `gmail.readonly` scope are required to run integration tests and live message fetching for the Gmail connector. Until provisioned, local execution must rely on mock message fixtures.

## Resolution Criteria

- Google Cloud Console OAuth 2.0 Client ID with `https://www.googleapis.com/auth/gmail.readonly` scope created.
- Loopback redirect URI (`http://localhost:8080/callback`) authorized in Cloud Console.
- Client secret and refresh token provisioned in secure keyring via `nyssa-ai-configuration` (or test environment variable).
- Live or recorded cassette test passes fetching real messages.

## Blocked Tasks

- [[../m3-ports-and-connectors/t4-gmail-oauth-flow|Gmail OAuth 2.0 authorization flow and token management]] <!-- ref: 019a4b2c-2000-7000-8000-000000000018 -->
- [[../m3-ports-and-connectors/t2-gmail-read-connector|Read-only Gmail connector using LangChain tool and Google API]] <!-- ref: 019a4b2c-2000-7000-8000-00000000000f -->

## External References

- Google Workspace API Console: `https://console.cloud.google.com/apis/credentials`
- Google OAuth 2.0 for Desktop Applications: `https://developers.google.com/identity/protocols/oauth2/native-app`
