---
id: 019a4b2c-2000-7000-8000-000000000003
type: milestone
record_version: 2
title: "Markdown Storage & CST Engine"
milestone-state: not-started
project_id: "019a4b2c-2000-7000-8000-000000000001"
created_at: "2026-11-03T11:30:00Z"
updated_at: "2026-11-03T11:30:00Z"
started_at: null
resolved_at: null
target_date: "2026-11-15"
tags: ["cst", "markdown", "parser", "writer", "obsidian"]
---
# [ ] M2: Markdown Storage & CST Engine · 2026-11-15

**Project:** [[../project-index|Daily Tasks Python MCP Server]] <!-- ref: 019a4b2c-2000-7000-8000-000000000001 -->

## Overview

Build the Concrete Syntax Tree (CST) parser and surgical writer for Obsidian-compatible Markdown records. The engine parses YAML scalar frontmatter, checklist items with hidden HTML comment IDs (`<!-- id: UUIDv7 -->`), table rows with wiki-links, and section headers. When applying updates from explicit user adjudication, the engine surgically toggles checkboxes, appends decision log entries, and updates metadata while preserving all original whitespace, comments, and user annotations byte-for-byte.

## Definition of Done

- [ ] Parser extracts DTO entities from canonical Markdown files (`4-sample-task.md` through `8-sample-daily-plan.md`) without data loss <!-- id: 019a4b2c-2000-7000-8000-00000000000c -->
- [ ] Surgical CST writer applies targeted state toggles and metadata updates preserving all unrelated lines and formatting <!-- id: 019a4b2c-2000-7000-8000-00000000000d -->
- [ ] Daily plan generator writes canonical 6-column `daily-plan.md` matching `8-sample-daily-plan.md` exactly <!-- id: 019a4b2c-2000-7000-8000-00000000000e -->

## Tasks

| # | Task | Status | Assignee | Due Date |
|---|---|---|---|---|
| 4 | [[t1-frontmatter-and-checklist-parser\|Scalar frontmatter, checklist ID, and wiki-link parser]] <!-- ref: 019a4b2c-2000-7000-8000-00000000000b --> | [ ] | jordan@example.com | 2026.11.11 |
| 5 | [[t2-surgical-markdown-writer\|Surgical CST writer and DoD checkbox toggling]] <!-- ref: 019a4b2c-2000-7000-8000-00000000000c --> | [ ] | jordan@example.com | 2026.11.13 |
| 6 | [[t3-daily-plan-generator\|Daily plan Markdown generator and template parity]] <!-- ref: 019a4b2c-2000-7000-8000-00000000000d --> | [ ] | jordan@example.com | 2026.11.15 |

## Blockers

None

## Status Legend

`[ ]` not started · `[>]` in progress · `[x]` completed · `[-]` cancelled
