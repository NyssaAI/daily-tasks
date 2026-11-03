---

id: 019a4b2c-2000-7000-8000-000000000016

type: task

record_version: 2

title: "Structured logging, end-to-end integration tests, and Tessl syndication"

task-state: not-started

owner: "jordan@example.com"

assignee: "jordan@example.com"

project_id: "019a4b2c-2000-7000-8000-000000000001"

milestone_id: "019a4b2c-2000-7000-8000-000000000007"

created_at: "2026-11-03T11:30:00Z"

updated_at: "2026-11-03T11:30:00Z"

started_at: null

resolved_at: null

target_date: "2026-12-15"

tags: ["logging", "testing", "packaging", "tessl", "cli"]

---

# Structured logging, end-to-end integration tests, and Tessl syndication



**Milestone:** [[m6-mcp-server-and-packaging|MCP Stdio Server & Packaging]] <!-- ref: 019a4b2c-2000-7000-8000-000000000007 -->



**Project:** [[../project-index|Daily Tasks Python MCP Server]] <!-- ref: 019a4b2c-2000-7000-8000-000000000001 -->



## Requirements



Finalize the Python MCP server package for distribution, skill documentation, and syndication:

1. Integrate `nyssa-ai-logging` and `nyssa-ai-configuration` ensuring all diagnostic logs emit to `sys.stderr` with structured context (session ID, correlation ID).

2. Build end-to-end integration tests exercising real session workflows from start to finish against a sample vault.

3. Establish CLI entrypoint `daily-tasks-mcp` defined in `pyproject.toml` (`[project.scripts]`).

4. Update canonical instructions under `skills/` (specifically `skills/daily-tasks-setup/SKILL.md` for connector setup and first-run Gmail OAuth onboarding, plus `skills/daily-tasks-plan/SKILL.md`, `skills/daily-tasks/SKILL.md`, and `skills/daily-tasks-checkin/SKILL.md`) to document MCP tool invocations (`daily_tasks_start_session`, `daily_tasks_execute_operations`, `daily_tasks_advance_screen`, `daily_tasks_confirm_plan`) while preserving strict "no time-fitting, no implicit acceptance" guardrails.

5. Regenerate host plugin manifests and bundled distribution artifacts via `node scripts/assemble.mjs write` per `AGENTS.md`.

6. Ensure all project files under `projects/2026.11.03-daily-tasks-mcp-server/` are ready for Tessl syndication.



## Definition of Done



- [ ] Structured logging configured via `nyssa-ai-logging` strictly writing to stderr <!-- id: 019a4b2c-2000-7000-8000-00000000003c -->

- [ ] Comprehensive integration test suite passes running full session lifecycle end-to-end <!-- id: 019a4b2c-2000-7000-8000-00000000003d -->

- [ ] Canonical instructions in `skills/` (including `daily-tasks-setup` connector onboarding and `daily-tasks-plan` MCP workflows) updated and host manifests regenerated via `node scripts/assemble.mjs write` <!-- id: 019a4b2c-2000-7000-8000-00000000003e -->

- [ ] CLI entry point callable via `uv run daily-tasks-mcp` or `python -m daily_tasks.server` <!-- id: 019a4b2c-2000-7000-8000-00000000003f -->



## Inputs



- `src/daily_tasks/server/mcp_server.py`.

- `pyproject.toml`.



## Work Product



- Python files: `src/daily_tasks/cli.py`, `src/daily_tasks/logging_setup.py`.

- Integration tests: `tests/integration/test_full_planning_session.py`.



## Depends on



- [[t1-mcp-tools-exposition|MCP tool protocols exposition and stdio JSON-RPC transport]] <!-- ref: 019a4b2c-2000-7000-8000-000000000015 -->



## Required by



None



## Blocked by



None

