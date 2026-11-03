---

id: 019a4b2c-2000-7000-8000-000000000004

type: milestone

record_version: 2

title: "Pluggable Ports & Communication Adapters"

milestone-state: in-progress

project_id: "019a4b2c-2000-7000-8000-000000000001"

created_at: "2026-11-03T11:30:00Z"

updated_at: "2026-11-03T11:30:00Z"

started_at: null

resolved_at: null

target_date: "2026-11-22"

tags: ["ports", "adapters", "langchain", "connectors", "gmail", "slack"]

---

# [ ] M3: Pluggable Ports & Communication Adapters · 2026-11-22



**Project:** [[../project-index|Daily Tasks Python MCP Server]] <!-- ref: 019a4b2c-2000-7000-8000-000000000001 -->



## Overview



Establish the hexagonal port architecture (`ProjectPlanPort`, `DailyPlanPort`, `CommunicationPort`, `LocalFileStore`) following the specifications in `docs/PLANNING_SESSION_CONCEPT.md`. Implement read-only communication connectors using LangChain tools (deterministic API fetchers with zero runtime LLM API calls) for Gmail and Slack. Implement persistent JSON cursor tracking (`fetch-cursors.json`) to guarantee incremental message ingestion.



## Definition of Done



- [ ] Python `typing.Protocol` classes defined for `ProjectPlanPort`, `DailyPlanPort`, `CommunicationPort`, and `LocalFileStore` <!-- id: 019a4b2c-2000-7000-8000-000000000018 -->

- [ ] Gmail and Slack read-only adapters fetch messages and map to canonical `Message` DTOs without requiring LLM keys <!-- id: 019a4b2c-2000-7000-8000-000000000019 -->

- [ ] Cursor persistence manager stores and reloads source watermarks conforming to `fetch-cursors.json` <!-- id: 019a4b2c-2000-7000-8000-00000000001a -->



## Tasks



| # | Task | Status | Assignee | Due Date |

|---|---|---|---|---|

| 7 | [[t1-port-protocols-and-file-sources\|Port protocol definitions and Markdown file sources]] <!-- ref: 019a4b2c-2000-7000-8000-00000000000e --> | [ ] | jordan@example.com | 2026.11.18 |

| 8 | [[t4-gmail-oauth-flow\|Gmail OAuth 2.0 authorization flow and token management]] <!-- ref: 019a4b2c-2000-7000-8000-000000000018 --> | [ ] | sarah@example.com | 2026.11.19 |

| 9 | [[t2-gmail-read-connector\|Read-only Gmail connector using LangChain tool and Google API]] <!-- ref: 019a4b2c-2000-7000-8000-00000000000f --> | [ ] | sarah@example.com | 2026.11.20 |

| 10 | [[t3-slack-read-connector-and-cursors\|Read-only Slack connector and cursor persistence]] <!-- ref: 019a4b2c-2000-7000-8000-000000000010 --> | [ ] | alex@example.com | 2026.11.22 |



## Blockers



| # | Status | Blocker | Blocks | Owner |

|---|---|---|---|---|

| B1 | [ ] | [[../blockers/b1-gmail-oauth-credentials-provisioning\|Gmail read-only OAuth credentials provisioning]] <!-- ref: 019a4b2c-2000-7000-8000-000000000017 --> | #8, #9 | jordan@example.com |



## Status Legend



`[ ]` not started · `[>]` in progress · `[x]` completed · `[-]` cancelled

