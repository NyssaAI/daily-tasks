# Product

## Purpose

Daily Tasks is a personal task management and daily planning system that lets people maintain projects, milestones, accepted tasks, external blockers, and daily plans in human-editable files while reviewing and updating their work with an AI assistant. It exists so individuals can stay in control of their own and delegated commitments—including updates arriving through email and chat—without surrendering ownership to an autonomous assistant or forcing tasks into calendar time blocks.

## Audience

- **Individual knowledge workers and technical leads** who manage personal and delegated work across projects, milestones, tasks, and external blockers in a local workspace or knowledge vault, and who want fast, structured daily planning and anytime check-ins.
- **Calling AI assistants** that invoke Daily Tasks workflows and planning session operations on the user's behalf while preserving explicit user confirmation for every new commitment or record change.

## Problem

Action items, status changes, and blockers arrive fragmented across chat messages, emails, and meeting notes. Existing task tools either lock commitments inside opaque cloud databases, automatically accept inferred promises without the user's consent, or try to schedule work into rigid calendar time slots and duration estimates. Meanwhile, maintaining plain-text project notes manually makes it difficult to carry unfinished work forward from day to day, reconcile direct file edits with assistant-driven updates, or keep an auditable history of what was decided and why.

## Solution

Daily Tasks combines six focused workflow skills (request routing, workspace setup, candidate capture, record management, daily planning, and anytime check-in) with a deterministic three-screen daily planning session:

1. **Editable Work Records**: Every project, milestone, task, external blocker, and daily plan lives as a readable, directly editable document in the user's workspace. Each milestone and task carries its own Definition of Done checklist, and changes preserve the user's existing notes and formatting.
2. **Candidate Capture & Explicit Acceptance**: Possible commitments extracted from notes, emails, or messages remain candidates until the user explicitly accepts, edits, or rejects them individually or in a batch.
3. **Three-Screen Interactive Daily Planning**:
   - **Screen 1 (Plan the Day & Suggested Updates)**: Carries unfinished selections forward (`↺`) from the previous daily plan, gathers unread email and chat messages in the background, matches them to active work, and presents numbered update suggestions (new tasks, status changes, Definition of Done checks, and blockers) with cited message sources.
   - **Screen 2 (Assign Tasks to Days)**: Steps through open projects one at a time so the user can assign plannable tasks and blocker follow-ups to today or future dates, delegate ownership, and update statuses using compact numbered replies.
   - **Screen 3 (Confirm Today's Plan)**: Summarizes today's personal work, delegated work, and active blockers for final review before writing the dated daily plan.
4. **Anytime Check-In & Reconciliation**: Users can check in at any point during the day to report progress, reconcile manual checkbox or text edits, resolve conflicts, and update today's plan.

## Planning Session & Deterministic Architecture

The planning session operates as a deterministic tool service with explicit separation between assistant reasoning, deterministic matching, and validated persistence:

### Architectural Decisions

- **Deterministic Server**: The planning session server executes deterministic logic only (graph compilation, message pre-matching, stage-machine validation, and atomic writes). It makes no internal LLM calls and requires no API keys.
- **Host-Driven Reasoning**: The calling assistant host (such as Codex, Claude, Cursor, or Antigravity) handles natural-language understanding, turns message snippets into structured proposals, and translates user replies into structured decisions.
- **Pluggable Ports Architecture**: Read operations are delegated to pluggable, concurrent port protocols (`ProjectPlanPort`, `DailyPlanPort`, `CommunicationPort`), while all mutations pass exclusively through `LocalFileStore`.
- **Read-Only Connectors & Existing Assistant Connections**: Communication integrations operate in strictly read-only mode—either reusing email/chat connections already available in the user's assistant environment or connecting via standalone read-only connectors—using shared incremental watermark checkpoints and a configurable first-pull lookback window (defaulting to no more than 7 days) without any capability to send, reply, or draft outbound messages.
- **Explicit Acceptance Invariant**: No suggestion is applied without an explicit answer from the user. Bare numbers without an action require clarification and are never treated as acceptance.

### Planning Session Process Flow

```text
"Let's plan the day"
│
├── collect_current_state                                    [server]
│   ├── 1. Gather Project Information: Project-Plan-Port
│   ├── 2. Gather Daily Plan Information: Daily-Plan-Port
│   └── 3. Build State Graph (in-memory, point-in-time snapshot)
│
├── gather_planning_messages                (background)     [server]
│   ├── 1. Gather Email: Communication-Port
│   ├── 1. Gather Slack: Communication-Port
│   └── 2. Persist Messages: Local File Store (message files + message log)
│
├── reconcile_messages
│   ├── 1. Pre-match (background, deterministic)             [server]
│   │   ├── drop messages already processed (by message ID)
│   │   ├── link each message to candidate tasks: task refs/links,
│   │   │   thread IDs seen before, sender = assignee, project/task title matches
│   │   └── flag signal words: done / merged / blocked / waiting on / can you
│   ├── 2. Propose suggestions                               [Assistant LLM]
│   │   └── reads pre-matched messages + state graph → proposes
│   │       status updates, new tasks, blockers (each cites its message)
│   └── 3. Save suggestions: Local File Store                [server]
│       └── validated, numbered stably, stored as pending
│
├── display_planning_screen                                  [server]
│   ├── 1. Organize State Graph, build initial screen
│   ├── 2. If pre-match incomplete → 'Still analyzing messages'
│   ├── 2. If complete → show suggestions (numbered, with source message)
│   └── 3. Show counts: open projects, tasks, blockers
│
├── adjudicate_suggestions
│   ├── 1. User replies by row number and legend symbol      [user]
│   │   Reply by row number and symbol or description:
│   │   Legend: [ ] not started · [>] in progress · [x] completed · [-] cancelled
│   │   (blocker rows: [ ] open · [x] completed (resolved))
│   ├── 2. Turn reply into decisions: accept / reject / edit [Assistant LLM]
│   └── 3. Apply decisions                                   [server]
│       ├── accepted → write records (validated against state graph)
│       ├── rejected → logged in the decision log; message stays in the message log
│       └── log each decision; nothing unanswered is applied
│
├── process_open_work         (repeat until user says done)
│   ├── 1. User directs: "move 7 to Thursday", "5 is blocked on legal"
│   ├── 2. Turn into operations                              [Assistant LLM]
│   │   └── assign_to_day · set_status · add/clear blocker · reassign
│   └── 3. Validate + apply each operation, return updated screen [server]
│
└── finalize_plan                                            [server]
    └── write YYYY.MM.DD-daily-plan.md (active template)
```

### Ports & Storage Authority

- **Project-Plan-Port** (`MarkdownProjectSource`): Read-only scanner of `projects/**/*.md`.
- **Daily-Plan-Port** (`MarkdownDailyPlanSource`): Read-only reader of `daily-plans/YYYY.MM.DD-daily-plan.md`.
- **Communication-Port** (`GmailSource`, `SlackSource`, and existing assistant-connected communication sources): Read-only sources fetching messages incrementally since last watermark cursor (or bounded to the configured initial lookback window, defaulting to 7 days, on the first pull).
- **Local File Store** (`MarkdownFileStore`): Authorized to apply validated record writes and daily plans exclusively following explicit user adjudication.

### Session Lifecycle & Persistence Rules

- **Canonical State**: Markdown records in `projects/` and `daily-plans/`.
- **Session State**: Session snapshot (stage, per-source fetch cursors, pending suggestions, row mappings) under `.nyssa-ai/daily-tasks/`.
- **Message Log & Cursors**: Every fetched message is persisted and logged once (`<messages_root>/message-log.json`). Logged messages are never re-fetched. Messages remain unreviewed until their suggestions are adjudicated or reported non-actionable.
- **Context Budget**: Messages passed to the assistant are trimmed (sender, subject, short snippet, linked task IDs, signal flags).
- **Stage-Gated Tools**: Calls made out of sequence return a structured `refused` response naming the expected next tool.

## Boundaries

- **No time-fitting or calendar scheduling**: Daily Tasks never estimates task durations, fits work into available hours, or blocks calendar slots. The person chooses execution order.
- **No implicit acceptance**: Quoted requests, inferred promises, message suggestions, or bare row numbers without an action never create or mutate records without an explicit user decision.
- **Not an autonomous persona**: Daily Tasks supplies capabilities to the user's chosen assistant rather than acting as an independent background agent.
- **Strictly read-only communication access**: Email and chat integrations only read incoming messages to propose updates; they never send, reply to, or draft outbound messages.
- **No mandatory cloud service**: Personal and project records remain local to the user's chosen workspace without requiring an external task database.

## Success

- Users can complete a full daily planning session—reviewing carried-forward tasks, adjudicating message-derived suggestions, assigning open project tasks to days, and confirming today's plan—using short numbered replies.
- Direct manual edits to projects, milestones, tasks, blockers, and daily plans are preserved without losing user comments or formatting, and conflicts are surfaced clearly during check-in.
- Every accepted, edited, or rejected suggestion and planning operation is recorded in an append-only decision history with clear attribution.
- Unanswered message suggestions and unreviewed communications survive interrupted sessions and reappear cleanly in the next planning session without duplicate fetching or data loss.

## Core Concepts & Macro-Flows

Foundational domain concepts and end-to-end macro-flows are maintained in `docs/concepts/` alongside legacy reference notes in [CONCEPTS.md](CONCEPTS.md) and [PLANNING_SESSION_CONCEPT.md](PLANNING_SESSION_CONCEPT.md):

- [C-01: Canonical Work Records & Embedded Definition of Done](concepts/c-01-canonical-work-records.md) — Project, Milestone, Task, and Blocker lifecycles, embedded completion checklists, and surgical preservation of user edits.
- [C-02: Local-Day Plan, Rollover & Carried Selections](concepts/c-02-local-day-plan-and-rollover.md) — Dated daily plan views, once-per-day carry-forward (`↺`), personal vs. delegated work separation, and blocker follow-ups without time-fitting.
- [C-03: Explicit Adjudication & Decision Log](concepts/c-03-explicit-adjudication-and-decision-log.md) — Candidate vs. accepted work, numbered-row batch replies, zero implicit acceptance, and append-only decision history.
- [C-04: Three-Screen Planning Session Macro-Flow](concepts/c-04-three-screen-planning-session.md) — Point-in-time state snapshot, background communication ingestion, deterministic pre-matching, and the Screen 1 → Screen 2 → Screen 3 planning lifecycle.

## Features

The feature catalog and detailed feature guides are maintained in [features.md](features.md) and `docs/features/`.

## Tech Stack

Runtime, framework, storage, tooling, and environment choices are maintained separately in [tech-stack.md](tech-stack.md).
