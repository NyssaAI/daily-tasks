# Planning Session: Deterministic MCP Server

## Decisions

- **Python MCP server, deterministic.** The server makes no LLM calls and needs no API key.
- **The host does the reasoning.** Codex (or any MCP client) proposes suggestions and turns the user's replies into structured decisions. The server collects, pre-matches, validates and writes.
- **Pluggable ports.** Python `Protocol`s, with as many implementations per port as are configured. All configured implementations run concurrently.
- **Connectors may wrap LangChain tools.** Read-only tools only, called directly (no agent).
- **No LangGraph, no DSPy.** Flow control is a small explicit state machine on `asyncio`.
- **Explicit acceptance only.** No suggestion is applied without an answer from the user.

## Process

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
│   ├── 2. Propose suggestions                               [Codex LLM]
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
│   ├── 2. Turn reply into decisions: accept / reject / edit [Codex LLM]
│   └── 3. Apply decisions                                   [server]
│       ├── accepted → write records (validated against state graph)
│       ├── rejected → logged in the decision log; message stays in the message log
│       └── log each decision; nothing unanswered is applied
│
├── process_open_work         (repeat until user says done)
│   ├── 1. User directs: "move 7 to Thursday", "5 is blocked on legal"
│   ├── 2. Turn into operations                              [Codex LLM]
│   │   └── assign_to_day · set_status · add/clear blocker · reassign
│   └── 3. Validate + apply each operation, return updated screen [server]
│
└── finalize_plan                                            [server]
    └── write YYYY.MM.DD-daily-plan.md (active template)
```

Suggestion rows and replies follow the existing legend and numbered-reply protocol in [response-conventions.md](../skills/daily-tasks/references/response-conventions.md): one continuous 1-based row sequence, stable numbers within the session, batch replies such as `1 x, 2 >, 3 -`, and a bare number with no symbol or action is never treated as acceptance.

`gather_planning_messages` and pre-matching start in the background as soon as `collect_current_state` finishes. The planning screen is shown without waiting for them.

## Ports

```python
class ProjectPlanPort(Protocol):
    name: str
    async def fetch_projects(self) -> list[Project]: ...

class DailyPlanPort(Protocol):
    name: str
    async def fetch_plans(self, around: date) -> list[DailyPlan]: ...

class CommunicationPort(Protocol):
    name: str
    async def fetch_messages(self, since: datetime) -> list[Message]: ...

class LocalFileStore(Protocol):
    def save_state_graph(self, graph: StateGraph) -> None: ...
    def save_messages(self, source: str, messages: list[Message]) -> None: ...
    def save_suggestions(self, session_id: str, suggestions: list[Suggestion]) -> None: ...
    def apply(self, changes: list[RecordChange]) -> None: ...      # validated writes
    def write_daily_plan(self, plan: DailyPlan) -> None: ...
```

| Port | Default implementation | Reads / writes |
|---|---|---|
| Project-Plan-Port | `MarkdownProjectSource` | `projects/**/*.md` |
| Daily-Plan-Port | `MarkdownDailyPlanSource` | `daily-plans/YYYY.MM.DD-daily-plan.md` |
| Communication-Port | `GmailSource` (LangChain Gmail toolkit, read-only) | Gmail |
| Communication-Port | `SlackSource` (optional) | Slack |
| Local File Store | `MarkdownFileStore` | markdown records + `.nyssa-ai/daily-tasks/` |

Ports that read are read-only. All writes go through the Local File Store.

## MCP tools

| Tool | Stage | Notes |
|---|---|---|
| `plan_start(user_note?)` | collect_current_state | Builds the state graph, starts background gather + pre-match, returns `session_id` and the planning screen |
| `plan_screen(session_id)` | display_planning_screen | Returns `Still analyzing messages` until pre-match completes; then returns the message graph's `for_review` list for Codex to reconcile, or saved suggestions if already submitted |
| `plan_suggest(session_id, suggestions)` | reconcile_messages (3) | Validates each suggestion against the state graph and its cited message; saves with stable numbers |
| `plan_adjudicate(session_id, decisions)` | adjudicate_suggestions | Applies accepted/edited items, logs every decision (including rejections) |
| `plan_apply(session_id, operations)` | process_open_work | `assign_to_day`, `set_status`, `add_blocker`, `clear_blocker`, `reassign`; returns the updated screen |
| `plan_finalize(session_id)` | finalize_plan | Writes the daily plan using the active template |

Calls made in the wrong stage are refused with a message naming the expected next tool.

## State

- **Canonical:** markdown files in `projects/` and `daily-plans/`.
- **Session:** small JSON record (stage, per-source `since` cursors, pending suggestions) under `.nyssa-ai/daily-tasks/`.
- **Messages:** persisted on fetch, so a server restart doesn't lose them. If the server restarts mid-fetch, `plan_screen` starts the fetch again.
- **Message log:** every fetched message is logged once (day, message ID, location, reviewed). A logged message is never fetched again. Messages with `reviewed: false` are offered again in the next session, so a crash before review loses nothing. A message is marked reviewed once it is adjudicated or Codex reports no suggestion for it; what was decided lives in the decision log.
- **Messages root:** configurable (`messages_root` in port config); messages and downloaded attachments are stored beneath it.
- **Context budget:** messages passed to Codex are trimmed (sender, subject, short snippet, linked task IDs, signal flags).

## Connectors

- Wrap LangChain integrations behind `CommunicationPort`, or use the raw SDK where simpler.
- Expose read-only operations only; never send or draft.
- Each connector is an optional extra (`daily-tasks[gmail]`, `daily-tasks[slack]`).
- One failing connector is reported on the screen and doesn't block the others.

## Future option

If the host supports MCP **sampling** (the server borrows the host's model, no separate key), `reconcile_messages` step 2 can move into the background so suggestions are ready when the screen is shown.

## Open questions

1. **Markdown write ownership.** Resolved: `AGENTS.md` updated to authorize the deterministic MCP server's `LocalFileStore` to apply validated record writes and daily plans exclusively following explicit user adjudication.
2. **Reuse vs. port.** Call the existing Node `src/core/*` from Python, or port it to Python?
3. **Gmail auth.** Where the OAuth token is stored and how first-run sign-in happens.
4. **Plugin root path.** Confirm how Codex resolves the server's launch path in `.mcp.json`.
