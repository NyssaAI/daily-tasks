---
id: F-03.01
group: "03"
status: implemented
---

# F-03.01 Workflow Skill Routing & Host Bundle Distribution

## Summary

Route user requests to the appropriate Daily Tasks workflow skill and package ready-to-install skill bundles across supported AI assistant environments.

## User Need

Users want to ask naturally to set up their workspace, capture commitments, update records, plan their day, or check in across their preferred AI coding or chat client, with only the relevant workflow loaded and optional index prewarming available.

## Conceptual Context

None.

## Use Cases

None yet.

## Scope

- Route incoming user requests through the top-level `daily-tasks` skill to the specific child workflow (`setup`, `capture`, `records`, `plan`, or `checkin`) without loading unnecessary instructions.
- Allow each of the six skills to be invoked directly or composed when a request spans multiple workflows (such as check-in followed by record updates and daily planning).
- Assemble and verify host-specific plugin manifests and distribution bundles from the single canonical `skills/` source.
- Provide an optional, silent project-index prewarm command for supported hosts that refreshes stale inventory metadata without invoking an assistant model or sending chat messages.

## Out of Scope

- Acting as an autonomous background persona or initiating unprompted conversations with the user.
- Claiming host activation from file packaging alone without host registration.

## Inputs

- Canonical skill instructions, references, and templates under `skills/`.
- User natural-language requests in a supported AI assistant host.

## Outputs

- Routed workflow execution in the calling assistant.
- Generated and verified distribution bundles and manifests for supported assistant hosts.
- Fresh disposable project inventory cache when prewarmed or requested on demand.

## Acceptance

- Asking to set up, capture work, update records, plan the day, or check in loads only the corresponding workflow procedure.
- Generated host bundles match the canonical skill definitions and pass bundle integrity verification checks.
- Disabling or omitting the optional prewarm automation affects only startup latency; every workflow still verifies inventory freshness on demand.

## Dependencies

- [F-00.01: Workspace, Identity & Template Setup](../f-00.01/feature.md)
