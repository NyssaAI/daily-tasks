---
id: 019a4b2c-2000-7000-8000-00000000000c
type: task
record_version: 2
title: "Surgical CST writer and DoD checkbox toggling"
task-state: not-started
owner: "jordan@example.com"
assignee: "jordan@example.com"
project_id: "019a4b2c-2000-7000-8000-000000000001"
milestone_id: "019a4b2c-2000-7000-8000-000000000003"
created_at: "2026-11-03T11:30:00Z"
updated_at: "2026-11-03T11:30:00Z"
started_at: null
resolved_at: null
target_date: "2026-11-13"
tags: ["cst", "writer", "markdown", "surgical-edit"]
---
# Surgical CST writer and DoD checkbox toggling

**Milestone:** [[m2-markdown-storage-and-cst-engine|Markdown Storage & CST Engine]] <!-- ref: 019a4b2c-2000-7000-8000-000000000003 -->

**Project:** [[../project-index|Daily Tasks Python MCP Server]] <!-- ref: 019a4b2c-2000-7000-8000-000000000001 -->

## Requirements

Implement the surgical CST writer component for applying validated record changes:
1. Locate specific checklist items by `<!-- id: UUIDv7 -->` and toggle status (`[ ]` -> `[x]`, `[>]`, etc.) without altering adjacent text.
2. Update YAML frontmatter scalar fields (`task-state`, `updated_at`, `resolved_at`) while preserving comment headers, key ordering, and whitespace.
3. Append decision log entries into the `## Decisions` or `## Decision Log` section.
4. Verify non-destructive modification: running a surgical write on an unedited file results in a byte-identical output.

## Definition of Done

- [ ] Surgical writer toggles individual checklist items by ID without modifying any other lines <!-- id: 019a4b2c-2000-7000-8000-000000000012 -->
- [ ] Frontmatter updates alter only targeted scalar values and `updated_at` timestamps <!-- id: 019a4b2c-2000-7000-8000-000000000013 -->
- [ ] Zero diff property test verifies unedited lines, trailing whitespace, and line-endings (LF/CRLF) remain intact <!-- id: 019a4b2c-2000-7000-8000-000000000014 -->

## Inputs

- `src/daily_tasks/storage/cst/parser.py` AST/CST nodes.
- `docs/specs/4-sample-task.md` and `docs/specs/record-change.json`.

## Work Product

- Python files: `src/daily_tasks/storage/cst/writer.py`, `src/daily_tasks/storage/cst/mutations.py`.
- Unit tests: `tests/storage/test_surgical_writer.py`.

## Depends on

- [[t1-frontmatter-and-checklist-parser|Scalar frontmatter, checklist ID, and wiki-link parser]] <!-- ref: 019a4b2c-2000-7000-8000-00000000000b -->

## Required by

- [[../m5-session-state-machine-and-adjudication/t2-adjudication-and-decision-log|Operation validation, suggestion pruning, and decision log append]] <!-- ref: 019a4b2c-2000-7000-8000-000000000014 -->

## Blocked by

None
