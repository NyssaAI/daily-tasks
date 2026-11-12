---
id: F-03.01
group: "03"
status: implemented
---

# F-03.01 Workflow Skill Routing & Host Bundle Distribution

## Summary

Route user requests to the appropriate Daily Tasks workflow and package ready-to-install skill bundles across supported AI assistant environments.

## User Need

Users want to ask naturally to set up their vault, capture commitments, update records, plan their day, or check in across their preferred AI coding or chat client, with only the relevant workflow loaded.

## Conceptual Context

None.

## Use Cases

None yet.

## Scope

- Route incoming user requests through the encapsulated `daily-tasks` facade skill to the specific child workflow (`setup`, `capture`, `records`, `plan`, or `checkin`) without loading unnecessary instructions.
- Allow workflows to compose cleanly when a request spans multiple steps (such as check-in followed by record updates and daily planning).
- Assemble and verify host-specific `harness-adapter` manifests and staged distribution bundles (`.temp/dist/`) from the single canonical `skills/` source.

## Out of Scope

- Acting as an autonomous background persona or initiating unprompted conversations with the user.
- Claiming host activation from file packaging alone without host registration.

## Inputs

- Canonical skill instructions, workflows, references, and templates under `skills/daily-tasks/`.
- User natural-language requests in a supported AI assistant host.

## Outputs

- Routed workflow execution in the calling assistant.
- Generated and verified `harness-adapter` manifests and staged distribution bundles for supported assistant hosts.

## Acceptance

- Asking to set up, capture work, update records, plan the day, or check in loads only the corresponding workflow procedure.
- Generated host bundles match the canonical skill definitions and pass bundle integrity verification checks.

## Dependencies

- [F-00.01: Vault, Identity & Template Setup](../f-00.01/feature.md)
