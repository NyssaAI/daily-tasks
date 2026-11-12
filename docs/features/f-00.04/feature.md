---
id: F-00.04
group: "00"
status: implemented
---

# F-00.04 Existing Assistant Connection Discovery & Bounded Lookback Retrieval

## Summary

Detect email and chat connections already available in the user's AI assistant environment during setup, let the user choose which connections to use and configure their initial lookback window (defaulting to no more than 7 days on the first pull), and process messages from existing connections using the exact same incremental checkpoints and suggestion workflows as built-in connections.

## User Need

Users who already have their email or team chat connected in their AI assistant environment do not want to set up duplicate credentials or re-authorize a separate communication client just for daily planning, nor do they want their first planning session overwhelmed by months of historical emails. They need setup to detect what is already connected, ask which source they prefer, cap the first pull to at most 7 days by default (with the option to customize that window), and track incremental checkpoints identically so every subsequent pull only reads new messages.

## Conceptual Context

- [C-03: Explicit Adjudication & Decision Log](../../concepts/c-03-explicit-adjudication-and-decision-log.md) — ensures messages fetched through an existing assistant connection produce the same numbered, source-cited candidate suggestions requiring explicit user adjudication.
- [C-04: Three-Screen Planning Session Macro-Flow](../../concepts/c-04-three-screen-planning-session.md) — supplies bounded first-pull and incremental subsequent-pull messages during Stage 0 using shared per-source checkpoints and updates those checkpoints upon Screen 3 confirmation.

## Use Cases

- [UC-00.04.01: Discover Available Communication Connections and Configure Initial Lookback Window](uc-00.04.01-discover-connections-and-configure-lookback.md)
- [UC-00.04.02: Fetch Messages Through Existing Assistant Connection Using Shared Checkpoints](uc-00.04.02-fetch-messages-via-existing-connection.md)

## Scope

- Inspect the user's assistant environment during setup to identify already-connected email and chat integrations alongside available standalone read-only connections.
- Ask the user which available communication connection(s) they want to use for daily planning, or whether to leave message retrieval disabled.
- Bound the first message pull for any source without a prior checkpoint to no more than 7 days by default, and allow the user to configure a custom initial lookback window in days.
- Provide the active fetch window (starting from the saved source checkpoint on subsequent runs, or from the configured initial lookback cutoff on the first run) so existing assistant connections retrieve only messages within that window.
- Apply the exact same deduplication, checkpoint filtering, project and task correlation, signal detection, numbered suggestion generation, and checkpoint advancement to messages fetched through an existing assistant connection as to messages from built-in communication clients.
- Enforce strictly read-only usage across existing assistant connections, never invoking any action that sends, replies to, drafts, modifies, or deletes external messages.

## Out of Scope

- Authorizing or keeping standalone credentials when the user chooses to rely exclusively on an existing assistant connection (standalone credentials are owned by [F-00.03](../f-00.03/feature.md)).
- Sending, replying to, forwarding, or modifying emails or chat messages in the user's connected accounts.
- Automatically accepting or applying any message-derived update without explicit user adjudication on Screen 1 (owned by [F-02.01](../f-02.01/feature.md) and [F-02.02](../f-02.02/feature.md)).

## Inputs

- Available email and chat integrations detected in the user's assistant environment and any existing standalone connection settings.
- User selection of which communication connection(s) to enable (existing assistant connection, standalone read-only connection, or none).
- User preference for the initial lookback window in days (defaulting to 7 days when not specified).
- Saved per-source incremental checkpoints (`since` timestamp and last processed message identifier) when present.

## Outputs

- Saved communication source preferences and configurable initial lookback window setting in the user's profile.
- Explicit per-source fetch window bounds (cutoff timestamp and last processed message identifier) honoring the 7-day default (or user-configured lookback) on the first pull and the saved checkpoint on subsequent pulls.
- Normalized message records correlated into numbered Screen 1 update suggestions and updated per-source checkpoints persisted when the daily plan is confirmed.

## Acceptance

- During setup, the assistant identifies any email or chat connections already available in the assistant environment, presents the options clearly, and records the user's chosen connection mode.
- On the first pull for a communication source with no prior checkpoint, no messages older than 7 days are pulled by default, and changing the configured lookback window adjusts that first-pull cutoff accordingly.
- Messages retrieved via an existing assistant connection undergo the same checkpoint filtering, task/project matching, and Screen 1 suggestion numbering as standalone clients, and confirming the plan advances the same per-source checkpoint so already-processed messages are never pulled again.
- Existing assistant connections are used exclusively to read incoming messages and never trigger outbound messages or mailbox modifications.

## Dependencies

- [F-00.01: Vault, Identity & Template Setup](../f-00.01/feature.md)
- [F-00.03: Credential Privacy & Read-Only Communication Connections](../f-00.03/feature.md)
