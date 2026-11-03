# Planning session type examples

JSON examples of the types that are persisted or non-trivial, for design review. See [PLANNING_SESSION_CONCEPT.md](../PLANNING_SESSION_CONCEPT.md) for the process.

All examples share IDs and match the workflow screens. Timestamps are GMT ISO ending in `Z`; IDs are UUIDv7. `{"$ref": "..."}` points at another example instead of repeating it.

| File | Type | Persisted where |
|---|---|---|
| [project.json](project.json) | Project | Markdown frontmatter (`projects/YYYY.MM.DD-<title>/project-index.md`) |
| [milestone.json](milestone.json) | Milestone | Markdown frontmatter + DoD |
| [task.json](task.json) | Task | Markdown frontmatter + DoD + relations |
| [blocker.json](blocker.json) | Blocker | Markdown frontmatter (`impact`, `resolved_when`) |
| [daily-plan.json](daily-plan.json) | DailyPlan + entries (tasks & blockers) | `daily-plans/YYYY.MM.DD-daily-plan.md` |
| [state-graph.json](state-graph.json) | StateGraph (point-in-time, in memory) | Not persisted; rebuilt from markdown |
| [message.json](message.json) | Message (record with attachments) | `<messages_root>/YYYY-MM-DD/<source>/<id>/message.json` |
| [message-log.json](message-log.json) | Message log (day, message ID, location, reviewed) | `<messages_root>/message-log.json` |
| [message-graph.json](message-graph.json) | MessageGraph (point-in-time, in memory) | Not persisted; rebuilt from message log + message files |
| [fetch-cursors.json](fetch-cursors.json) | FetchCursor (per source) | `.nyssa-ai/daily-tasks/fetch-cursors.json` |
| [suggestions.json](suggestions.json) | Pending suggestions buffer | `.nyssa-ai/daily-tasks/suggestions.json` (temporary until acted on) |
| [decision-log.json](decision-log.json) | Decision log (all entries with decided_by/at) | `.nyssa-ai/daily-tasks/decision-log.json` (append-only) |
| [decision-log-entry.json](decision-log-entry.json) | DecisionLogEntry (one entry) | Shape of each entry in `decision-log.json` |
| [operations.json](operations.json) | Operation (transient request to `plan_apply`) | Transient payload format |
| [record-change.json](record-change.json) | RecordChange (write-ahead checkpoint) | Transient write-ahead buffer |
| [planning-session.json](planning-session.json) | PlanningSession (screens, order, row maps) | `.nyssa-ai/daily-tasks/sessions/YYYY.MM.DD.json` |
| [1-plan-the-day-screen.md](1-plan-the-day-screen.md) | PlanningScreen 1 mockup | Returned by `plan_start` / `plan_screen` |
| [2-assign-days-screen.md](2-assign-days-screen.md) | PlanningScreen 2 mockup (assign days & updates) | Returned by `plan_apply` |
| [3-confirm-plan-screen.md](3-confirm-plan-screen.md) | PlanningScreen 3 mockup (confirm plan) | Returned before `plan_finalize` |
| [4-sample-task.md](4-sample-task.md) | Sample Task Markdown record (metadata + body with `<!-- id -->` & `<!-- ref -->`) | Persistent task file (`projects/.../tN-name.md`) |
| [5-sample-project-index.md](5-sample-project-index.md) | Sample Project Index Markdown record | Persistent project index file (`projects/.../project-index.md`) |
| [6-sample-milestone.md](6-sample-milestone.md) | Sample Milestone Markdown record | Persistent milestone file (`projects/.../mN-name.md`) |
| [7-sample-blocker.md](7-sample-blocker.md) | Sample Blocker Markdown record | Persistent blocker file (`projects/.../blockers/bN-name.md`) |
| [8-sample-daily-plan.md](8-sample-daily-plan.md) | Sample Daily Plan Markdown record | Persistent daily plan file (`daily-plans/YYYY.MM.DD-daily-plan.md`) |
| [tool-results.json](tool-results.json) | ToolResult wrappers (`processing`/`ok`/`refused`/`error`) | Tool responses |
| [port-config.json](port-config.json) | PortConfig | Profile extension |

## Rules & Decisions Implemented

- **Project Ordering**: Project directories use `YYYY.MM.DD-<title>` format; sorted ascending by date prefix.
- **Blocker Scheduling**: Blockers can be scheduled for a day (`item_type: "blocker"`). If scheduled for today, they appear in today's user tasks.
- **Suggestion Storage**: Stored in `.nyssa-ai/daily-tasks/suggestions.json`. Unacted suggestions stay there across sessions; acted ones move to `decision-log.json` and are pruned from the file.
- **Decision Log Schema**: Uses `decided_by` and `decided_at` explicitly.
- **Screen-Scoped Numbering**: Session maintains `screens: { <screen_id>: { ... } }` ensuring row numbers on screen 3 (restarting at 1) do not collide with session-wide numbered screens 1 and 2.
