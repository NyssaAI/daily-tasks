---
id: 01a1a2d0-c698-7c5f-bf20-8d41e24c2442
type: task
record_version: 2
title: "Storage CST modules refactoring and PY-FILE naming alignment"
task-state: not-started
owner: "sarah@example.com"
assignee: "sarah@example.com"
project_id: "019a4b2c-2000-7000-8000-000000000001"
milestone_id: "01a1a2d0-c698-74c1-8867-99b2df28c504"
created_at: "2026-11-03T13:10:00Z"
updated_at: "2026-11-03T13:10:00Z"
started_at: null
resolved_at: null
target_date: "2026-11-16"
tags: ["refactoring", "cst", "dev-standards", "storage"]
---
# Storage CST modules refactoring and PY-FILE naming alignment

**Milestone:** [[m2.5-secrets-and-encapsulation-refactor|Storage CST Standards Alignment & In-Memory Secrets Architecture]] <!-- ref: 01a1a2d0-c698-74c1-8867-99b2df28c504 -->

**Project:** [[../project-index|Daily Tasks Python MCP Server]] <!-- ref: 019a4b2c-2000-7000-8000-000000000001 -->

## Requirements

Refactor the modules in `src/daily_tasks/storage/cst/` so they strictly satisfy the Single Responsibility and module naming rules (`PY-FILE`, `PY-HEADER`) of `.nyssa-ai/dev-standards/python/`:
1. Rename parser and writer modules to match their primary function export:
   - `parser.py` -> `parse_markdown.py` (exporting `parse_markdown`)
   - `writer.py` -> `write_markdown.py` (exporting `write_markdown`)
   - `daily_plan_renderer.py` -> `render_daily_plan.py` (exporting `render_daily_plan`)
2. Refactor `mutations.py` along cohesive boundaries into single-function modules:
   - `set_checklist_mark.py`
   - `set_frontmatter_field.py`
   - `append_decision.py`
3. Refactor `nodes.py` so each syntax node lives in its own module named after the node class (`markdown_document.py`, `heading.py`, `source_line.py`, etc.) or group pure DTOs cleanly under `types.py`.
4. Ensure `src/daily_tasks/storage/cst/__init__.py` re-exports all public CST APIs via `__all__`.
5. Update all unit tests and verify 100% pass under `check.py` without diagnostics.

## Definition of Done

- [ ] All modules under `src/daily_tasks/storage/cst/` conform to `PY-FILE` (filenames match primary class/function export) <!-- id: 01a1a2d0-c698-7c5f-bf20-8d41e24c2443 -->
- [ ] Every file includes synchronized ASCII interface trees (`PY-HEADER`) <!-- id: 01a1a2d0-c698-7c5f-bf20-8d41e24c2444 -->
- [ ] All 68 existing tests pass with 0 regressions <!-- id: 01a1a2d0-c698-7c5f-bf20-8d41e24c2445 -->

## Inputs

- `src/daily_tasks/storage/cst/` modules.
- `.nyssa-ai/dev-standards/python/rules/standards.md`.

## Work Product

- Refactored Python files under `src/daily_tasks/storage/cst/`.
- Updated unit tests under `test/unit/daily_tasks/storage/`.

## Depends on

- [[../m2-markdown-storage-and-cst-engine/m2-markdown-storage-and-cst-engine|Markdown Storage & Concrete Syntax Tree Engine]] <!-- ref: 019a4b2c-2000-7000-8000-000000000003 -->

## Required by

- [[../m3-ports-and-connectors/m3-ports-and-connectors|Pluggable Ports & Communication Adapters]] <!-- ref: 019a4b2c-2000-7000-8000-000000000004 -->
