---
id: C-03
type: domain-model
status: active
---

# C-03: Explicit Adjudication & Decision Log

## Summary

Daily Tasks enforces a strict boundary between candidate proposals and accepted commitments: no project, milestone, task, blocker, or status change is ever persisted from notes, emails, or chat messages without an explicit user decision. Every user verdict and planning operation is recorded in an append-only decision log with full attribution.

## Core Model / Stages

- **Candidate vs. Accepted Work**: Action items extracted from notes, quoted requests, inferred promises, or incoming messages begin as **Candidates** or **Pending Suggestions** (`new_task`, `status`, `dod`, `blocker`). Only a direct user instruction to create named work or an explicit `accept` / `edit` verdict promotes a candidate into a canonical record change.
- **Numbered Row Protocol**: Interactive planning and review screens assign stable 1-based integers to every displayed task, blocker, and suggestion row. Users reply with compact batch instructions (such as `3 accept, 4 accept but due Friday, 7 reject` or `14 today, 12 done`).
- **Verdict (`accept` | `reject` | `edit`)**: The user's explicit adjudication of a pending suggestion. Accepted and edited suggestions stage validated record changes and prune the suggestion from the pending buffer; rejected suggestions are logged and pruned without modifying records.
- **Decision Log Entry**: An immutable decision record in `runtime_root` capturing the question or suggestion presented, the user's original words, the structured decision (`accept`, `reject`, `edit`, or direct operation), the actor who decided (`decided_by`), the timestamp (`decided_at`), and the affected record or message references.

## Invariants & Rules

- **No Implicit Acceptance**: A bare row number without an action or status symbol requires clarification and is never treated as acceptance. Unanswered suggestions remain pending across sessions; nothing unanswered is ever applied.
- **Message Review Coupling**: A fetched email or chat message is marked `reviewed` only after its linked suggestion is explicitly adjudicated by the user (or when analysis determines it contains no actionable suggestion). If a session ends or crashes before adjudication, the message and its suggestion reappear in the next session.
- **All-or-Nothing Batch Validation**: If any verdict or operation in a batch fails validation (such as an invalid row number, wrong screen scope, or unmet completion criteria), the entire batch is refused with a clear explanation and no state is mutated.
- **Append-Only Decision History**: Existing entries in the decision log are never overwritten or deleted.

## Participating Features

- [F-01.01: Candidate Work Capture & Deduplication](../features/f-01.01/feature.md) — holds extracted action items as candidates until the user explicitly accepts them individually or in a batch.
- [F-01.02: Project, Milestone, Task & Blocker Lifecycle Management](../features/f-01.02/feature.md) — validates state changes and completion rules before applying adjudicated record mutations.
- [F-02.01: Communication Correlation & Update Suggestions](../features/f-02.01/feature.md) — generates numbered, source-cited suggestions in the pending buffer without auto-applying them.
- [F-02.02: Three-Screen Daily Planning & Day Assignment](../features/f-02.02/feature.md) — adjudicates suggestions, executes numbered planning operations, and appends entries to the decision log.
