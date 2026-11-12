# Product

## Purpose

Daily Tasks is a personal task management and daily planning system that lets people maintain projects, milestones, accepted tasks, external blockers, and daily plans in human-editable files while reviewing and updating their work with an AI assistant. It exists so individuals can stay in control of their own and delegated commitments—including updates arriving through email and chat—without surrendering ownership to an autonomous assistant or forcing tasks into calendar time blocks.

## Audience

- **Individual knowledge workers and technical leads** who manage personal and delegated work across projects, milestones, tasks, and external blockers in a local or shared knowledge vault, and who want fast, structured daily planning and anytime check-ins.
- **Calling AI assistants** that invoke Daily Tasks workflows and planning session operations on the user's behalf while preserving explicit user confirmation for every new commitment or record change.

## Problem

Action items, status changes, and blockers arrive fragmented across chat messages, emails, and meeting notes. Existing task tools either lock commitments inside opaque cloud databases, automatically accept inferred promises without the user's consent, or try to schedule work into rigid calendar time slots and duration estimates. Meanwhile, maintaining plain-text project notes manually makes it difficult to carry unfinished work forward from day to day, reconcile direct file edits with assistant-driven updates, or keep an auditable history of what was decided and why.

## Solution

Daily Tasks combines an encapsulated `daily-tasks` facade skill and five focused workflows (vault setup, candidate capture, record management, daily planning, and anytime check-in) with a deterministic three-screen daily planning session:

1. **Editable Work Records**: Every project, milestone, task, external blocker, and daily plan lives as a readable, directly editable document in the user's vault (`vault_root`). Each milestone and task carries its own Definition of Done checklist, and changes preserve the user's existing notes and formatting.
2. **Candidate Capture & Explicit Acceptance**: Possible commitments extracted from notes, emails, or messages remain candidates until the user explicitly accepts, edits, or rejects them individually or in a batch.
3. **Three-Screen Interactive Daily Planning**:
   - **Screen 1 (Plan the Day & Suggested Updates)**: Carries unfinished selections forward (`↺`) from the previous daily plan, gathers unread email and chat messages in the background, matches them to active work, and presents numbered update suggestions (new tasks, status changes, Definition of Done checks, and blockers) with cited message sources.
   - **Screen 2 (Assign Tasks to Days)**: Steps through open projects one at a time so the user can assign plannable tasks and blocker follow-ups to today or future dates, delegate ownership, and update statuses using compact numbered replies.
   - **Screen 3 (Confirm Today's Plan)**: Summarizes today's personal work, delegated work, and active blockers for final review before writing the dated daily plan.
4. **Anytime Check-In & Reconciliation**: Users can check in at any point during the day to report progress, reconcile manual checkbox or text edits, resolve conflicts, and update today's plan.

## Planning Session & Deterministic Architecture

The planning session operates as a deterministic tool service with explicit separation between assistant reasoning, deterministic matching, and validated persistence:

### Architectural Decisions

- **Deterministic Server**: The planning session server executes deterministic logic only (graph compilation, message pre-matching, stage-machine validation, and atomic writes). It makes no internal LLM calls and requires no LLM API keys.
- **Host-Driven Reasoning**: The calling assistant host (such as Codex, Claude, Cursor, Hermes, or Antigravity) handles natural-language understanding, turns message snippets into structured proposals, and translates user replies into structured decisions.
- **Scale B SOLID Modular Monolith & Role-Named Contracts**: Pure domain logic and consumer-owned collaborator contracts (`ProjectPlanRepository`, `DailyPlanRepository`, `FileStore`, `CommunicationClient`, `SuggestionsRepository`, `CursorStore`, `PlanningDispatcher`) live in `core/`, while entity-first implementations (`ProjectPlanRepositoryMarkdown`, `DailyPlanRepositoryMarkdown`, `FileStoreLocal`, `CommunicationClientGmail`, `CommunicationClientSlack`, `SuggestionsRepositoryJson`, `CursorStoreJson`) live in isolated feature slices.
- **Read-Only Communication Clients & Existing Assistant Connections**: Communication integrations operate in strictly read-only mode—either reusing email/chat connections already available in the user's assistant environment or connecting via standalone read-only clients—using shared incremental fetch cursors in `runtime_root` and a configurable first-pull lookback window (defaulting to no more than 7 days) without any capability to send, reply, or draft outbound messages.
- **Explicit Acceptance Invariant**: No suggestion is applied without an explicit answer from the user. Bare numbers without an action require clarification and are never treated as acceptance.

### Planning Session Process Flow

```text
"Let's plan the day"
│
├── collect_current_state                                    [server]
│   ├── 1. Gather Project Information: ProjectPlanRepository
│   ├── 2. Gather Daily Plan Information: DailyPlanRepository
│   └── 3. Build State Graph (in-memory, point-in-time snapshot)
│
├── gather_planning_messages                (background)     [server]
│   ├── 1. Gather Email: CommunicationClient (Gmail or host pass-through)
│   └── 2. Gather Slack: CommunicationClient (Slack or host pass-through)
│
├── reconcile_messages
│   ├── 1. Pre-match (background, deterministic)             [server]
│   │   ├── drop messages already processed (by cursor / message ID)
│   │   ├── link each message to candidate tasks: task refs/links,
│   │   │   thread IDs seen before, sender = assignee, project/task title matches
│   │   └── flag signal words: done / merged / blocked / waiting on / can you
│   ├── 2. Propose suggestions                               [Assistant LLM]
│   │   └── reads pre-matched messages + state graph → proposes
│   │       status updates, new tasks, blockers (each cites its message)
│   └── 3. Save suggestions: SuggestionsRepository           [server]
│       └── validated, numbered stably, persisted as pending in runtime_root
│
├── display_planning_screen                                  [server]
│   ├── 1. Organize State Graph, build initial screen
│   ├── 2. Show suggestions (numbered, with source message)
│   └── 3. Show counts: open projects, tasks, blockers
│
├── adjudicate_suggestions
│   ├── 1. User replies by row number and legend symbol      [user]
│   │   Reply by row number and symbol or description:
│   │   Legend: [ ] not started · [>] in progress · [x] completed · [-] cancelled
│   │   (blocker rows: [ ] open · [x] completed (resolved))
│   ├── 2. Turn reply into decisions: accept / reject / edit [Assistant LLM]
│   └── 3. Apply decisions                                   [server]
│       ├── accepted → stage record changes (validated against state graph)
│       ├── rejected → logged in the decision log
│       └── log each decision; nothing unanswered is applied
│
├── process_open_work         (repeat until user says done)
│   ├── 1. User directs: "move 7 to Thursday", "5 is blocked on legal"
│   ├── 2. Turn into operations                              [Assistant LLM]
│   │   └── assign_to_day · set_status · add/clear blocker · reassign
│   └── 3. Validate + apply each operation, return updated screen [server]
│
└── finalize_plan                                            [server]
    └── write YYYY.MM.DD-daily-plan.md + staged RecordChanges via FileStore
```

### Collaborator Contracts & Persistence Authority

- **`ProjectPlanRepository`** (`ProjectPlanRepositoryMarkdown`): Read-only scanner of `<vault_root>/1-projects/**/*.md` (or configured `projectsRoot`).
- **`DailyPlanRepository`** (`DailyPlanRepositoryMarkdown`): Read-only reader of `<vault_root>/2-areas/daily-plans/YYYY.MM.DD-daily-plan.md` (or configured `dailyPlansRelative`).
- **`CommunicationClient`** (`CommunicationClientGmail`, `CommunicationClientSlack`, and existing assistant-connected communication sources): Read-only clients fetching messages incrementally since last `FetchCursor` (or bounded to the configured initial lookback window, defaulting to 7 days, on the first pull).
- **`FileStore`** (`FileStoreLocal`): Authorized to apply validated `RecordChange` edits and daily plans inside `vault_root` exclusively following explicit user adjudication.

### Session Lifecycle & 5-Root Persistence Rules

- **Canonical Vault State (`vault_root`)**: Markdown records in `1-projects/` and `2-areas/daily-plans/`. Zero `.nyssa-ai/` files or runtime state live inside `vault_root`.
- **Configuration (`user_home` -> `repo_root`)**: User and vault bindings live in `~/.nyssa-ai/daily-tasks/profile.json` (and optional `<repo_root>/.nyssa-ai/daily-tasks/profile.json`).
- **Mutable Operational State (`runtime_root`)**: Session snapshots (`sessions/`), per-source fetch cursors (`fetch-cursors.json`), pending suggestions (`suggestions.json`), and append-only `decision-log.json` live strictly in `runtime_root`.
- **Context Budget**: Messages passed to the assistant are trimmed (sender, subject, short snippet, linked task IDs, signal flags).
- **Stage-Gated Tools**: Calls made out of sequence return a structured `refused` response naming the expected next tool.

## Boundaries

- **No time-fitting or calendar scheduling**: Daily Tasks never estimates task durations, fits work into available hours, or blocks calendar slots. The person chooses execution order.
- **No implicit acceptance**: Quoted requests, inferred promises, message suggestions, or bare row numbers without an action never create or mutate records without an explicit user decision.
- **Not an autonomous persona**: Daily Tasks supplies capabilities to the user's chosen assistant rather than acting as an independent background agent.
- **Strictly read-only communication access**: Email and chat integrations only read incoming messages to propose updates; they never send, reply to, or draft outbound messages.
- **No mandatory cloud service**: Personal and project records remain local to the user's chosen vault without requiring an external task database.

## Success

- Users can complete a full daily planning session—reviewing carried-forward tasks, adjudicating message-derived suggestions, assigning open project tasks to days, and confirming today's plan—using short numbered replies.
- Direct manual edits to projects, milestones, tasks, blockers, and daily plans are preserved without losing user comments or formatting, and conflicts are surfaced clearly during check-in.
- Every accepted, edited, or rejected suggestion and planning operation is recorded in an append-only decision history with clear attribution.
- Unanswered message suggestions and unreviewed communications survive interrupted sessions and reappear cleanly in the next planning session without duplicate fetching or data loss.

## Core Concepts & Macro-Flows

Foundational domain concepts and end-to-end macro-flows are maintained in `docs/concepts/` alongside the authoritative lexicon in [GLOSSARY.md](GLOSSARY.md):

- [C-01: Canonical Work Records & Embedded Definition of Done](concepts/c-01-canonical-work-records.md) — Project, Milestone, Task, and Blocker lifecycles, embedded completion checklists, and non-destructive preservation of user edits.
- [C-02: Local-Day Plan, Rollover & Carried Selections](concepts/c-02-local-day-plan-and-rollover.md) — Dated daily plan views, once-per-day carry-forward (`↺`), personal vs. delegated work separation, and blocker follow-ups without time-fitting.
- [C-03: Explicit Adjudication & Decision Log](concepts/c-03-explicit-adjudication-and-decision-log.md) — Candidate vs. accepted work, numbered-row batch replies, zero implicit acceptance, and append-only decision history.
- [C-04: Three-Screen Planning Session Macro-Flow](concepts/c-04-three-screen-planning-session.md) — Point-in-time state snapshot, background communication retrieval, deterministic pre-matching, and the Screen 1 → Screen 2 → Screen 3 planning lifecycle.

## Features

The feature catalog and detailed feature guides are maintained in [features.md](features.md) and `docs/features/`.

## Tech Stack

Runtime, framework, persistence, tooling, and environment choices are maintained separately in [tech-stack.md](tech-stack.md).
