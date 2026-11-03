# 3. Confirm today's plan — screen mockup

Mockup of the recap shown after "yes" to *Ready to finalize today's plan?* (or "finish" on screen 2). It lists only the tasks planned for today, exactly as they will be written. Covers the `finalize_plan` stage.

---
> **Daily plan — Tuesday 2026.11.03** · America/Chicago
>
> **Planned today: 5**          **Mine: 3**          **Delegated: 2**          **Late: 0**
>
> <!-- if: pending_items -->
> ⚠ **1 suggestion still unanswered** (Draft connector README blocked by OAuth app verification). It stays pending if you confirm now.
> <!-- endif -->
>
> ## My work
>
> | # | Status | Project | Milestone | Task | Assignee | Due Date | Notes |
> | --- | --- | --- | --- | --- | --- | --- | --- |
> | 1 | [ ] | Daily Tasks MCP Server | Planning session spike | ✚ Review Slack connector PR | jordan@example.com | 2026.11.05 | |
> | 2 | [>] | Daily Tasks MCP Server | Connectors | Slack connector | jordan@example.com | 2026.11.12 | |
> | 3 | [ ] | Cloud Sync | Auth | ✚ Rotate staging API keys | jordan@example.com | — | |
>
> ## Delegated work
>
> | # | Status | Project | Milestone | Task | Assignee | Due Date | Notes |
> | --- | --- | --- | --- | --- | --- | --- | --- |
> | 4 | [>] | Daily Tasks MCP Server | Planning session spike | ↺ Wire Gmail connector | sarah@example.com | 2026.11.05 | ⛔ OAuth app verification |
> | 5 | [>] | Daily Tasks MCP Server | Planning session spike | Background fetch survives turns | alex@example.com | — | waits on #4 |
>
> <!-- if: blockers_for_today -->
> ## Blockers
>
> | # | Status | Blocker | Blocks | Owner | Resolved when |
> | --- | --- | --- | --- | --- | --- |
> | 6 | [ ] | Google OAuth app verification | #4 Wire Gmail connector | jordan@example.com | Google approves the OAuth app. |
>
> Legend: [ ] open · [x] completed (resolved)
> <!-- endif -->
>
> ## Confirm
>
> - "Confirm" (writes `daily-plans/2026.11.03-daily-plan.md`)
> - "Remove 3 from today" · "Move 2 to tomorrow"
> - "1 done" · "2 in progress" · "assign 3 to alex@example.com" · "6 resolved"
> - "Back to Cloud Sync" (return to screen 2 for that project)
>
> **Confirm today's plan?**

---

## Notes

- **Today only.** Lists every task planned for today, plus open blockers on those tasks. Tasks planned for other days, unrelated blockers and the decisions list are not shown here (all blockers and decisions are still written to the plan file).
- **Blockers** appear only when they block a task planned for today; "Blocks" names the affected rows. They continue the numbering (6) so "6 resolved" works.
- **Grouping.** My work = assigned to me. Delegated = I own it, someone else is assigned.
- **Assignee** is shown on every row, including my own work.
- **Numbering restarts at 1** on this screen. Numbers from screens 1 and 2 no longer apply once the recap is shown; the server binds replies to this screen's mapping and rejects old numbers. Going "back" to screen 2 restores the session numbers there.
- **Unanswered suggestions** don't block confirming. They stay pending and appear again next session; their messages stay unreviewed.
- **Small edits** (remove, move, assign, task/blocker status) apply here without leaving the screen; the recap refreshes and renumbers.
- **Confirm** writes the plan using the active `dailyPlan` template and ends the session. Saying "plan the day" again later the same day reopens it.
- **Hidden refs.** Each numbered row carries `<!-- ref: UUID -->` in the rendered markdown; omitted here for readability.
