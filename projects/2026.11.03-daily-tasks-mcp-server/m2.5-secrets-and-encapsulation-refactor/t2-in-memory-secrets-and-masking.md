---
id: 01a1a2d0-c698-7f13-b46a-45299030f034
type: task
record_version: 2
title: "In-memory secret holder, token provider, and sensitive field masking"
task-state: not-started
owner: "alex@example.com"
assignee: "alex@example.com"
project_id: "019a4b2c-2000-7000-8000-000000000001"
milestone_id: "01a1a2d0-c698-74c1-8867-99b2df28c504"
created_at: "2026-11-03T13:10:00Z"
updated_at: "2026-11-03T13:10:00Z"
started_at: null
resolved_at: null
target_date: "2026-11-17"
tags: ["secrets", "security", "tokens", "keyring"]
---
# In-memory secret holder, token provider, and sensitive field masking

**Milestone:** [[m2.5-secrets-and-encapsulation-refactor|Storage CST Standards Alignment & In-Memory Secrets Architecture]] <!-- ref: 01a1a2d0-c698-74c1-8867-99b2df28c504 -->

**Project:** [[../project-index|Daily Tasks Python MCP Server]] <!-- ref: 019a4b2c-2000-7000-8000-000000000001 -->

## Requirements

Implement in-memory secret holding and masking primitives leveraging `nyssa-ai-configuration` so credentials and tokens are never stored in plaintext on disk:
1. Deprecate disk-based `credentials_root` and `credentials_file` in `src/daily_tasks/domain/port_config.py` and `communication_binding.py`.
2. Implement `SecretString` or masked secret container that redacts token values from `repr()`, `str()`, and structured logging (`[REDACTED]`).
3. Wire integration with `nyssa_ai_configuration.KeyringInMemory` and `nyssa_ai_configuration.KeyringDefault` for runtime secret resolution from environment variables or OS credential vaults.
4. Provide unit tests proving secret strings are never leaked in string representations, JSON dumps without explicit secret export, or log outputs.

## Definition of Done

- [ ] `SecretString` wrapper prevents accidental leakage in `__repr__` and `__str__` <!-- id: 01a1a2d0-c698-7f13-b46a-45299030f035 -->
- [ ] Port configuration models deprecate disk credentials path in favor of in-memory keyring resolution <!-- id: 01a1a2d0-c698-7f13-b46a-45299030f036 -->
- [ ] Unit tests verify secret redaction and keyring resolution <!-- id: 01a1a2d0-c698-7f13-b46a-45299030f037 -->

## Inputs

- `nyssa-ai-configuration` keyring and OAuth contracts.
- `src/daily_tasks/domain/port_config.py`.

## Work Product

- Python files: `src/daily_tasks/domain/secret_string.py`, `src/daily_tasks/domain/port_config.py`.
- Unit tests: `test/unit/daily_tasks/domain/test_secret_string.py`.

## Depends on

- [[t1-cst-storage-standards-alignment|Storage CST modules refactoring and PY-FILE naming alignment]] <!-- ref: 01a1a2d0-c698-7c5f-bf20-8d41e24c2442 -->

## Required by

- [[../m3-ports-and-connectors/m3-ports-and-connectors|Pluggable Ports & Communication Adapters]] <!-- ref: 019a4b2c-2000-7000-8000-000000000004 -->
