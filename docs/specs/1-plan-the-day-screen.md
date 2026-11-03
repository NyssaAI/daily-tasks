# 1. Plan the day — screen mockup

Mockup of the screen `plan_start` / `plan_screen` returns. 

---
> **Open projects: 4**          **Open tasks: 18**          **Late tasks: 1**          **Blockers: 2**
>     - Tuesday 2026.11.03 · America/Chicago
> <!-- if: messages_analyzing -->
>     - ⏳ Still analyzing messages (Gmail done · Slack running). Ask again to see suggestions.
> <!-- endif -->
>
> ## Current PLan
>
> | # | Status | Project | Milestone | Task | Owner | Assignee | Due Date |
> | --- | --- | --- | --- | --- | --- | --- | --- |
> | 1 | [>] | Daily Tasks MCP Server | Planning session spike | ↺ Wire Gmail connector | jordan@example.com | sarah@example.com | 2026.11.05 |
> | 2 | [ ] | Daily Tasks MCP Server | Planning session spike | Background fetch survives turns | jordan@example.com | alex@example.com | — |
>
> <!-- if: suggestions_ready -->
> ## Suggested Updates (from messages)
>
> | # | Kind | Project | Milestone | Task | Current | Proposed | Why | Source |
> | --- | --- | --- | --- | --- | --- | --- | --- | --- |
> | 3 | New task | Daily Tasks MCP Server | Planning session spike | Review Slack connector PR | — | [ ] new · due 2026.11.05 | "can you review the Slack connector PR before Thursday?" | Slack · Alex · 2026.11.02 13:12 |
> | 4 | New task | Cloud Sync | Auth | Rotate staging API keys | — | [ ] new · assignee jordan@example.com | "please rotate the staging keys once the fix is out" | Gmail · Dana · 07:30 |
> | 5 | Status | Daily Tasks MCP Server | Planning session spike | Background fetch survives turns | [ ] | [>] | "started on the background fetch this morning" | Slack · Alex · 08:05 |
> | 6 | Status | Cloud Sync | Auth | Token refresh fix | [ ] | [x] | "token refresh fix is deployed to prod" | Gmail · Dana · 07:30 |
> | 7 | Status | Home Office | Network | Replace router | [>] | [-] | "landlord is replacing the router, no need" | Gmail · Pat · 2026.11.02 18:40 |
> | 8 | DoD | Daily Tasks MCP Server | Planning session spike | Wire Gmail connector | DoD 1/2 | DoD 2/2 · check "Read-only scopes only" | "read-only scopes are in" | Gmail · Sarah · 06:41 |
> | 9 | Blocker | Daily Tasks MCP Server | Planning session spike | Draft connector README | — | blocked by Google OAuth app verification | "waiting on Google's verification" | Gmail · Sarah · 06:41 |
> | 10 | Blocker | Cloud Sync | Auth | Token refresh fix | Vendor contract signature [ ] | [x] resolved | "contract is signed" | Gmail · Dana · 07:30 |
>
> Legend: [ ] not started · [>] in progress · [x] completed · [-] cancelled
>
> Reply `accept`, `reject`, or `edit` with the row numbers, for example:
>
> - "Accept all"
> - "3 accept, 4 accept but due Friday, 7 reject"
> - "5, 6, 8 accept · 9 reject · 10 accept"
> - "Show details for 6" (shows the full message)
> <!-- endif -->
>
> **Ready to review your open projects and tasks?** Reply "yes" to continue, or keep updating the items above.
>


---

## Notes

- **Stable numbers.** Rows 1–2 keep their numbers whether or not suggestions are shown; suggestions get the next free numbers (3–10) when they arrive, so earlier replies never change meaning.
- **Suggestion kinds.** New task (creates a record), Status (changes task state using the legend), DoD (checks criteria), Blocker (links, creates or resolves). Current → Proposed shows exactly what changes.
- **Nothing applies without an answer.** Unanswered suggestions stay pending; the message stays unreviewed.
- **Next step.** "Yes" to the review prompt moves to the open projects and tasks screen; pending suggestions carry over.
- **Hidden refs.** The rendered markdown carries `<!-- ref: UUID -->` on each task, blocker and suggestion row, as in the existing template; omitted here for readability.
- **Overdue.** Due dates in the past count toward Late tasks.
- **Failing connectors** are reported in the Suggested updates line and don't block the screen.
- **Open:** suggestion replies use `accept` / `reject` / `edit` until the legend question is decided.
