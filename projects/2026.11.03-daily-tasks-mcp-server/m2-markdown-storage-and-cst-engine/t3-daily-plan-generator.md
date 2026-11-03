---
id: 019a4b2c-2000-7000-8000-00000000000d
type: task
record_version: 2
title: "Daily plan Markdown generator and template parity"
task-state: not-started
owner: "jordan@example.com"
assignee: "jordan@example.com"
project_id: "019a4b2c-2000-7000-8000-000000000001"
milestone_id: "019a4b2c-2000-7000-8000-000000000003"
created_at: "2026-11-03T11:30:00Z"
updated_at: "2026-11-03T11:30:00Z"
started_at: null
resolved_at: null
target_date: "2026-11-15"
tags: ["daily-plan", "generator", "markdown", "template"]
---
# Daily plan Markdown generator and template parity

**Milestone:** [[m2-markdown-storage-and-cst-engine|Markdown Storage & CST Engine]] <!-- ref: 019a4b2c-2000-7000-8000-000000000003 -->

**Project:** [[../project-index|Daily Tasks Python MCP Server]] <!-- ref: 019a4b2c-2000-7000-8000-000000000001 -->

## Requirements

Implement the daily plan generator that formats a validated `DailyPlan` DTO into the canonical Obsidian Markdown record format matching `docs/specs/8-sample-daily-plan.md`.
The generator must:
1. Render YAML frontmatter with `type: daily-plan`, `local_day`, `started_at`, and `tags`.
2. Generate the 6-column `## My Work` table (`#`, `Task`, `Status`, `Project`, `Milestone`, `DoD Progress`).
3. Generate `## Blockers Under Active Resolution` table with `Blocker`, `Status`, `Project`, and `Resolution Objective`.
4. Generate `## Delegated Work Tracked` table with `Task`, `Owner`, `Assignee`, `Follow-up Trigger`, and `Communication Ref`.
5. Generate `## Decisions` section with bulleted record changes.

## Definition of Done

- [ ] Generates daily plan Markdown with identical structure, headers, and column names as `8-sample-daily-plan.md` <!-- id: 019a4b2c-2000-7000-8000-000000000015 -->
- [ ] Escapes table wiki-links correctly (`[[path\|alias]]`) and preserves all comment references <!-- id: 019a4b2c-2000-7000-8000-000000000016 -->
- [ ] Round-trip test: Generated Markdown can be parsed back into an equivalent `DailyPlan` DTO <!-- id: 019a4b2c-2000-7000-8000-000000000017 -->

## Inputs

- `docs/specs/8-sample-daily-plan.md`.
- `DailyPlan` DTO model from Milestone 1.

## Work Product

- Python files: `src/daily_tasks/storage/cst/daily_plan_renderer.py`.
- Unit tests: `tests/storage/test_daily_plan_renderer.py`.

## Depends on

- [[t1-frontmatter-and-checklist-parser|Scalar frontmatter, checklist ID, and wiki-link parser]] <!-- ref: 019a4b2c-2000-7000-8000-00000000000b -->

## Required by

- [[../m5-session-state-machine-and-adjudication/t2-adjudication-and-decision-log|Operation validation, suggestion pruning, and decision log append]] <!-- ref: 019a4b2c-2000-7000-8000-000000000014 -->

## Blocked by

None
