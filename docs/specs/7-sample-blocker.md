---
id: 019a4b2c-1f00-7a10-8000-000000000005
type: blocker
record_version: 2
title: "Google OAuth app verification"
blocker-state: open
impact: high
project_id: "019a4b2c-1f00-7a10-8000-000000000001"
created_at: "2026-10-29T14:15:00Z"
updated_at: "2026-11-02T19:00:00Z"
resolved_at: null
target_date: "2026-11-04"
tags: ["oauth", "security", "external"]
---
# B1 — Google OAuth app verification

**Project:** [[../project-index|Daily Tasks MCP Server]] <!-- ref: 019a4b2c-1f00-7a10-8000-000000000001 -->

## Impact & Summary

Google Cloud Console OAuth consent screen verification is pending security review for sensitive scopes (`gmail.readonly`). Until approved, connector testing is restricted to explicit test accounts (max 100 users) and throws unverified app warnings.

## Resolved When

- Security team submits privacy policy and YouTube demo video to Google Trust & Safety.
- Google Cloud Console status flips to "Verified".
- Production client credentials deployed to environment.

## Blocks

- [[../m2-planning-session-spike/t1-wire-gmail-connector|T1 — Wire Gmail connector behind Communication-Port]] <!-- ref: 019a4b2c-1f00-7a10-8000-000000000003 -->
- [[../m2-planning-session-spike/m2-planning-session-spike|M2 — Planning session spike]] <!-- ref: 019a4b2c-1f00-7a10-8000-000000000002 -->

## External References

- Support Ticket: https://console.cloud.google.com/apis/credentials/consent
- Tracking Thread: `https://nyssaai.slack.com/archives/C0812345/p1730554800001`
