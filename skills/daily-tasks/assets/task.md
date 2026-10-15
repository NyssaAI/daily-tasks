---
id: TASK_UUID
type: task
record_version: 2
title: "TASK_TITLE"
document-maturity: draft
task-state: not-started
owner: "OWNER_EMAIL"
project_id: "PROJECT_UUID"
milestone_id: "MILESTONE_UUID"
created_at: "GMT_TIMESTAMP"
updated_at: "GMT_TIMESTAMP"
---
# M1-T1 — TASK_TITLE

> Provisional template — evaluate on a real task before accepting this format.

**Milestone:** [[MILESTONE_SLUG|MILESTONE_TITLE]] <!-- ref: MILESTONE_UUID -->

**Project:** [[../project-index|PROJECT_TITLE]] <!-- ref: PROJECT_UUID -->

## Requirements

Describe what to build or change and why it matters.

## Definition of Done

- [ ] State an observable task acceptance criterion. <!-- id: TASK_CRITERION_UUID -->

## Inputs

- [[inputs/INPUT_FILE|Primary input]] — description and purpose.
<!--
Supporting context (as needed):
- Repository / branch / path: REPO_PATH or BRANCH_NAME
- Existing pattern / reference: PATH_OR_LINK
-->

## Work Product

<!--
Capture the work product directly here (inline decisions, findings, or notes),
prescribe execution steps/checklists if sequence matters, or link to deliverables:
- Execution steps / checklist (optional):
  1. [ ] First step
- Delivered files: [[outputs/OUTPUT_FILE]]
- Repository changes or PR: PULL_REQUEST_OR_BRANCH_LINK
-->

## Result

Summary of outcome and verification evidence.

## Depends on

- [[DEPENDENCY_TASK_SLUG|DEPENDENCY_TASK_TITLE]] <!-- ref: DEPENDENCY_TASK_UUID -->

## Required by

- [[DEPENDENT_TASK_SLUG|DEPENDENT_TASK_TITLE]] <!-- ref: DEPENDENT_TASK_UUID -->

## Blocked by

- [[../blockers/bBLOCKER_NUMBER-BLOCKER_SLUG|BLOCKER_TITLE]] <!-- ref: BLOCKER_UUID -->
