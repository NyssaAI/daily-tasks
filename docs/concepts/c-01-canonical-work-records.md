---
id: C-01
type: domain-model
status: active
---

# C-01: Canonical Work Records & Embedded Definition of Done

## Summary

All personal and delegated commitments in Daily Tasks are represented as canonical, human-editable work records—Projects, Milestones, Tasks, and Blockers (`RecordKind`)—maintained directly in the user's vault (`vault_root`). Each Milestone and Task embeds its own Definition of Done checklist criteria, and every automated update preserves user-authored prose, comments, and layout formatting intact.

## Core Model / Stages

- **Project**: The top-level container representing an outcome-oriented effort with an owner, lifecycle `state` (`not-started`, `in-progress`, `completed`, `cancelled`), optional target date, milestone index table, and project-wide blocker table.
- **Milestone**: A sequential delivery checkpoint (`M1`, `M2`, ...) belonging to a single Project. Owns an embedded Definition of Done checklist and an ordered table of child Tasks. The lowest incomplete milestone in a project is always eligible for daily planning; additional in-progress milestones can be included on request.
- **Task**: An atomic unit of accepted work belonging to a Milestone and Project. Carries an owner, optional assignee (defaulting to the owner when omitted), lifecycle `state`, optional target date, requirements, embedded Definition of Done criteria, task dependencies (`Depends on` / `Required by`), and blocker links (`Blocked by`).
- **Blocker**: An external condition belonging to a Project that prevents one or more Tasks or Milestones from completing. Tracks `state` (`open` or `resolved`), owner, impact description, resolution condition (`Resolved when`), and optional follow-up day assignment.
- **Embedded Definition of Done (DoD)**: Checklist items inside a Milestone or Task that define the exact completion criteria for that record. Each checklist item retains a stable identity across edits.

## Invariants & Rules

- **Single Canonical Authority**: Each project, milestone, task, and blocker has exactly one authoritative record file in the vault; daily plans and review screens are projections that reference canonical records without duplicating ownership.
- **Completion Guardrails**: A task cannot transition to `completed` until all of its embedded Definition of Done items are checked and all linked blockers are resolved. A milestone cannot transition to `completed` or `cancelled` while any of its child tasks remain open without an explicit decision for each open task.
- **Non-Destructive Edit Preservation**: Automated updates to record `state`, metadata, or Definition of Done checkboxes modify only the targeted fields and checklist markers while preserving unrelated user notes, comments, and whitespace byte-for-byte.
- **Responsibility Classification**: Relative to the user, an open task is classified as **My work** when assigned to the user (or unassigned and owned by the user), **Delegated work** when owned by the user and assigned to someone else, or **Follow-up** when owned by another person.

## Participating Features

- [F-00.01: Vault, Identity & Template Setup](../features/f-00.01/feature.md) — establishes vault roots and customizable document templates for each record kind.
- [F-00.02: Canonical Work Record Persistence & Non-Destructive Updates](../features/f-00.02/feature.md) — parses and non-destructively writes Project, Milestone, Task, and Blocker records without losing user edits.
- [F-01.02: Project, Milestone, Task & Blocker Lifecycle Management](../features/f-01.02/feature.md) — creates records and enforces status, Definition of Done, delegation, and blocker completion rules.
- [F-02.03: Anytime Check-In & Manual Edit Reconciliation](../features/f-02.03/feature.md) — reconciles manual checkbox and text edits in canonical records against daily plan views.
