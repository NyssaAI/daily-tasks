---
id: 019a4b2c-2000-7000-8000-00000000000b
type: task
record_version: 2
title: "Scalar frontmatter, checklist ID, and wiki-link parser"
task-state: not-started
owner: "jordan@example.com"
assignee: "jordan@example.com"
project_id: "019a4b2c-2000-7000-8000-000000000001"
milestone_id: "019a4b2c-2000-7000-8000-000000000003"
created_at: "2026-11-03T11:30:00Z"
updated_at: "2026-11-03T11:30:00Z"
started_at: null
resolved_at: null
target_date: "2026-11-11"
tags: ["cst", "parser", "markdown", "frontmatter"]
---
# Scalar frontmatter, checklist ID, and wiki-link parser

**Milestone:** [[m2-markdown-storage-and-cst-engine|Markdown Storage & CST Engine]] <!-- ref: 019a4b2c-2000-7000-8000-000000000003 -->

**Project:** [[../project-index|Daily Tasks Python MCP Server]] <!-- ref: 019a4b2c-2000-7000-8000-000000000001 -->

## Requirements

Develop a lossless Markdown CST parser that reads project files, milestone files, task files, blocker files, and daily plans. The parser must:
1. Extract YAML scalar frontmatter without modifying or dropping unknown fields.
2. Identify checklists (`- [ ]`, `- [>]`, `- [x]`, `- [-]`) and extract inline HTML comment IDs (`<!-- id: UUIDv7 -->`).
3. Parse Markdown tables with escaped wiki-links (`[[path\|alias]]`) and reference comments (`<!-- ref: UUIDv7 -->`).
4. Validate that parsed data maps cleanly to the Pydantic DTO models developed in M1.

## Definition of Done

- [ ] Parser extracts all frontmatter fields, checklist items, and table rows with line number tracking <!-- id: 019a4b2c-2000-7000-8000-00000000000f -->
- [ ] Round-trip parse tests successfully load `4-sample-task.md`, `5-sample-project-index.md`, `6-sample-milestone.md`, `7-sample-blocker.md`, and `8-sample-daily-plan.md` <!-- id: 019a4b2c-2000-7000-8000-000000000010 -->
- [ ] Gracefully reports parsing errors using `nyssa-ai-result` `Result[T, ParseError]` without crashing <!-- id: 019a4b2c-2000-7000-8000-000000000011 -->

## Inputs

- `docs/specs/4-sample-task.md` through `8-sample-daily-plan.md`.
- DTO models from Milestone 1.

## Work Product

- Python files: `src/daily_tasks/storage/cst/parser.py`, `src/daily_tasks/storage/cst/nodes.py`.
- Unit tests: `tests/storage/test_cst_parser.py`.

## Depends on

- [[../m1-dto-models-and-validation/t3-communications-and-graph-dtos|Communication, graph, and session DTO models]] <!-- ref: 019a4b2c-2000-7000-8000-00000000000a -->

## Required by

- [[t2-surgical-markdown-writer|Surgical CST writer and DoD checkbox toggling]] <!-- ref: 019a4b2c-2000-7000-8000-00000000000c -->
- [[../m3-ports-and-connectors/t1-port-protocols-and-file-sources|Port protocol definitions and Markdown file sources]] <!-- ref: 019a4b2c-2000-7000-8000-00000000000e -->

## Blocked by

None
