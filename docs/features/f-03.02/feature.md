---
id: F-03.02
group: "03"
status: complete
---

# F-03.02 Planning Session Tool Service & Host Integration

## Summary

Expose the deterministic daily planning session to AI assistant hosts as a standard tool service with clean diagnostic logging and end-to-end verification.

## User Need

Users and their AI assistants need a reliable local tool service that manages the multi-step daily planning session, enforces stage ordering and validation rules, and keeps diagnostic logs separate from assistant communication.

## Conceptual Context

- [C-04: Three-Screen Planning Session Macro-Flow](../../concepts/c-04-three-screen-planning-session.md) — exposes the session stages as structured tool calls for AI assistant hosts.

## Use Cases

- [UC-03.02.01: Run Interactive Planning Session Through Assistant Tool Service](uc-03.02.01-run-planning-session-via-assistant-tools.md)

## Scope

- Expose the daily planning session operations (`start_session`, `get_session_state`, `execute_operations`, `advance_screen`, `confirm_plan`, and `cancel_session`) to AI assistant hosts over a standard local tool protocol.
- Enforce stage-gated tool responses (`ok`, `refused` with expected next tool, or `error`) and keep all diagnostic logging on a separate diagnostic stream so tool responses remain clean.
- Provide a command-line entrypoint so assistant hosts can launch the planning session service directly from user configuration.
- Document the planning session tool workflow and communication onboarding in the canonical skills and stage host bundles.
- Verify the complete end-to-end session lifecycle against realistic vaults.

## Out of Scope

- Making language-model calls inside the planning session tool service (all language reasoning stays in the calling assistant host).
- Modifying vault records when a session is cancelled or before Screen 3 confirmation.

## Inputs

- Assistant tool requests carrying session IDs, user words, structured suggestion verdicts, planning operations, and screen transition targets.
- Vault path, runtime path, user identity, and timezone settings from user configuration or launch arguments.

## Outputs

- Structured tool responses containing the rendered planning screen Markdown, current stage, session ID, and operation counts.
- Separate structured diagnostic logs with session and request correlation.
- Updated skill instructions and regenerated host manifests.

## Acceptance

- An assistant host can launch the tool service, start a planning session, execute Screen 1 verdicts and Screen 2 day assignments, advance to Screen 3, and confirm the plan to produce `YYYY.MM.DD-daily-plan.md`.
- Out-of-order tool calls return a `refused` result naming the expected next tool without corrupting session state.
- Diagnostic logs never pollute the tool response stream.
- Canonical skill guides and assembled host manifests document the planning session tool workflow and pass all verification checks.

## Dependencies

- [F-00.02: Canonical Work Record Persistence & Non-Destructive Updates](../f-00.02/feature.md)
- [F-00.03: Credential Privacy & Read-Only Communication Connections](../f-00.03/feature.md)
- [F-02.01: Communication Correlation & Update Suggestions](../f-02.01/feature.md)
- [F-02.02: Three-Screen Daily Planning & Day Assignment](../f-02.02/feature.md)
- [F-03.01: Workflow Skill Routing & Host Bundle Distribution](../f-03.01/feature.md)
