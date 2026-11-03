---
id: F-02.01
group: "02"
status: implemented
---

# F-02.01 Communication Correlation & Update Suggestions

## Summary

Link unread emails and chat messages to matching projects, tasks, and blockers, detect progress or blocker signals, and propose numbered update suggestions citing the source message.

## User Need

Users want status updates, newly requested tasks, completed checklist items, and external blockers mentioned in email or chat to be surfaced automatically alongside the affected project and task during daily planning, with clear source attribution and zero changes applied until approved.

## Conceptual Context

- [C-03: Explicit Adjudication & Decision Log](../../concepts/c-03-explicit-adjudication-and-decision-log.md) — generates numbered, source-cited suggestions in the pending buffer without auto-applying them.
- [C-04: Three-Screen Planning Session Macro-Flow](../../concepts/c-04-three-screen-planning-session.md) — correlates ingested messages against the state graph to populate Screen 1's suggested updates.

## Use Cases

- [UC-02.01.01: Review and Adjudicate Message-Derived Suggestions on Screen 1](uc-02.01.01-review-and-adjudicate-message-suggestions.md)

## Scope

- Compile open projects, milestones, tasks, blockers, people, thread histories, and title terms into an in-memory state graph.
- Correlate unreviewed messages against the state graph using explicit record references, known thread IDs, sender/assignee relationships, and project/task title matches.
- Flag progress, completion, cancellation, blocker, and request signal phrases in matched messages.
- Generate and validate pending suggestions (`new_task`, `status`, `dod`, `blocker`) that cite their triggering message, quote the relevant snippet, and show `Current → Proposed` state changes.
- Number suggestions stably on Screen 1 after the current plan rows and retain unanswered suggestions across sessions until explicitly adjudicated.

## Out of Scope

- Fetching raw messages from external email or chat providers (owned by [F-00.03](../f-00.03/feature.md)).
- Applying any suggested update without an explicit user `accept` or `edit` verdict.

## Inputs

- In-memory state graph of current projects, milestones, tasks, and blockers.
- Unreviewed messages from the local message store and existing pending suggestions.

## Outputs

- Correlated message graph linking messages to candidate tasks, projects, and signal flags.
- Validated, stably numbered suggestions displayed on Screen 1 and persisted in the pending suggestions buffer until acted on.

## Acceptance

- Every suggestion displayed on Screen 1 cites its source message (channel, sender, timestamp, and reason quote) and clearly states the proposed change (`Current → Proposed`).
- Suggestions are assigned row numbers starting after the Current Plan rows so existing row numbers on Screen 1 never shift when message analysis finishes.
- Accepting, editing, or rejecting a suggestion logs the decision, prunes the suggestion from the pending buffer, and marks the source message reviewed; unanswered suggestions remain pending for the next session.

## Dependencies

- [F-00.02: Canonical Work Record Storage & Surgical Updates](../f-00.02/feature.md)
- [F-00.03: Credential Privacy & Read-Only Communication Connections](../f-00.03/feature.md)
- [F-01.02: Project, Milestone, Task & Blocker Lifecycle Management](../f-01.02/feature.md)
