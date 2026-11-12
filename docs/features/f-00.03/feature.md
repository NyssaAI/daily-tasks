---
id: F-00.03
group: "00"
status: implemented
---

# F-00.03 Credential Privacy & Read-Only Communication Connections

## Summary

Connect to email and team chat accounts in strictly read-only mode, keeping credentials protected in memory and tracking incremental message checkpoints so messages are never fetched twice.

## User Need

Users want incoming emails and chat messages to inform their daily planning without risking accidental outbound messages, exposing sensitive credentials in logs or plain-text files, or re-processing old messages every session.

## Conceptual Context

- [C-04: Three-Screen Planning Session Macro-Flow](../../concepts/c-04-three-screen-planning-session.md) — supplies incremental unread emails and chat messages during Stage 0 without blocking the session start.

## Use Cases

- [UC-00.03.01: Authorize Read-Only Communication Account](uc-00.03.01-authorize-readonly-communication-source.md)

## Scope

- Authorize and connect to configured email and team chat sources using strictly read-only permissions.
- Protect client secrets and authorization tokens in memory and sealed credential stores, masking sensitive values in all displays and diagnostic logs.
- Fetch messages concurrently across all configured communication sources starting from each source's saved watermark checkpoint.
- Track per-source fetch checkpoints and pending suggestions in runtime state so interrupted sessions never lose unreviewed items or re-fetch processed messages.
- Isolate communication client errors so a single unavailable or unauthenticated communication source is reported cleanly without blocking other sources or local planning.

## Out of Scope

- Sending, replying to, forwarding, or drafting emails or chat messages under any circumstance.
- Discovering already-connected assistant integrations or fetching messages through an existing assistant connection (owned by [F-00.04](../f-00.04/feature.md)).
- Matching fetched messages to tasks or proposing task updates (owned by [F-02.01](../f-02.01/feature.md)).

## Inputs

- User authorization approval and configured communication source credentials.
- Per-source incremental watermark checkpoints (`since` timestamps/cursors).

## Outputs

- Normalized, read-only message records with sender, recipients, subject, snippet, thread identifiers, and attachment metadata.
- Updated per-source fetch checkpoints in runtime state.
- Non-blocking source status indicators when a communication client succeeds or fails.

## Acceptance

- Connected communication sources request and exercise read-only access only and cannot send or modify external messages.
- Credentials and tokens never appear in plain text in vault files, chat output, or diagnostic logs.
- Messages up to the saved checkpoint are never fetched again on subsequent runs, while unreviewed suggestions remain available until adjudicated.
- When one communication source fails or times out, its failure is reported on the planning screen and all other sources and local planning proceed normally.

## Dependencies

- [F-00.01: Vault, Identity & Template Setup](../f-00.01/feature.md)
