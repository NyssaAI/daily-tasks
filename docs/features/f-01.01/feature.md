---
id: F-01.01
group: "01"
status: implemented
---

# F-01.01 Candidate Work Capture & Deduplication

## Summary

Extract possible tasks, milestones, and projects from notes, messages, or conversations, check them against existing work for duplicates, and hold them for explicit individual or batch acceptance.

## User Need

Users need a safe way to gather potential action items from meeting notes, messages, and discussions without cluttering their active project records with unapproved or duplicate tasks.

## Conceptual Context

- [C-03: Explicit Adjudication & Decision Log](../../concepts/c-03-explicit-adjudication-and-decision-log.md) — holds extracted action items as candidates until the user explicitly accepts them individually or in a batch.

## Use Cases

- [UC-01.01.01: Capture and Adjudicate Candidate Work](uc-01.01.01-capture-and-accept-candidate-work.md)

## Scope

- Extract candidate tasks, milestones, and projects from user-supplied notes, meeting transcripts, or messages.
- Compare extracted candidates against existing projects, milestones, and tasks to highlight potential duplicates or related open work.
- Present candidates in a numbered review list for individual or batch acceptance, editing, or rejection.
- Distinguish between inferred/quoted items (which must remain candidates until approved) and direct user instructions to create named work (which carry immediate acceptance).
- Hand accepted and edited items to [F-01.02](../f-01.02/feature.md) for record creation and log all decisions.

## Out of Scope

- Writing canonical project, milestone, or task files directly without user acceptance.
- Automated background retrieval of email and chat during the three-screen planning session (owned by [F-02.01](../f-02.01/feature.md)).

## Inputs

- User-supplied notes, messages, meeting summaries, or candidate lists.
- Existing project inventory for duplicate and parent-record matching.
- Explicit user decisions (`accept`, `edit`, or `reject`) by candidate number.

## Outputs

- Deduplicated candidate review list with proposed project/milestone placement and duplicate warnings.
- Hand-off of explicitly accepted items to record creation, plus logged rejection decisions.

## Acceptance

- Quoted requests, inferred promises, and action items extracted from notes never create or modify vault files until the user explicitly accepts them.
- Candidates that closely match an existing open task or milestone flag the existing record so the user can avoid creating duplicates.
- Users can accept, edit, or reject multiple candidates in a single batch reply, and unanswered candidates remain uncreated.

## Dependencies

- [F-00.01: Vault, Identity & Template Setup](../f-00.01/feature.md)
- [F-00.02: Canonical Work Record Persistence & Non-Destructive Updates](../f-00.02/feature.md)
