# 2. Assign tasks to days — screen mockup

Mockup of the screen shown after "yes" to *Ready to review your open projects and tasks?* One project per screen. Its main job is choosing **which day** each open task is planned for; while here you can also assign tasks and blockers and update the status of tasks, milestones and blockers. Structural project edits (DoD wording, new milestones, moving tasks) belong to a separate project update screen.

---
> **Project 1 of 4** · Tuesday 2026.11.03 · America/Chicago
>
> ## Daily Tasks MCP Server
>
>   - Python MCP server that runs the plan-the-day session with pluggable ports.
>     - M1: Design (complete)
>     - M2: Planning session spike (in progress)
>     - M3: Connectors (in progress)
>     - M4: Packaging (not started)
>
> <!-- if: include_in_progress_milestones -->
> Showing tasks from every in-progress milestone (M2, M3). Reply "only M2" to show just the lowest incomplete milestone.
> <!-- endif -->
> <!-- if: not include_in_progress_milestones -->
> Showing tasks from M2 only. Reply "include in-progress milestones" to also plan M3.
> <!-- endif -->
>
> ## M2: Planning session spike
>
> | # | Task | Status | Assignee | Due Date | Planned day | Notes |
> | --- | --- | --- | --- | --- | --- | --- |
> | 11 | ↺ Wire Gmail connector | [>] | sarah@example.com | 2026.11.05 | **Today** | ⛔ #18 OAuth app verification |
> | 12 | Background fetch survives turns | [>] | alex@example.com | — | **Today** | waits on #11 |
> | 13 | Draft connector README | [ ] | — | — | **Thu 2026.11.05** | ⛔ #18 OAuth app verification |
> | 14 | ✚ Review Slack connector PR | [ ] | — | 2026.11.05 | — | new from Slack · Alex |
>
> <!-- if: include_in_progress_milestones -->
> ## M3: Connectors
>
> | # | Task | Status | Assignee | Due Date | Planned day | Notes |
> | --- | --- | --- | --- | --- | --- | --- |
> | 15 | Slack connector | [>] | jordan@example.com | 2026.11.12 | — | |
> | 16 | Outlook connector | [ ] | — | — | — | waits on #15 |
> | 17 | Connector error reporting | [ ] | — | — | **Fri 2026.11.06** | |
> <!-- endif -->
>
> Legend: [ ] not started · [>] in progress · [x] completed · [-] cancelled · ↺ carried forward · ✚ added this session · ⛔ blocked
>
> ## Blockers
>
> | # | Status | Blocker | Blocks | Owner | Planned day |
> | --- | --- | --- | --- | --- | --- |
> | 18 | [ ] | Google OAuth app verification | #11, #13 | jordan@example.com | — |
>
> Legend: [ ] open · [x] completed (resolved)
>
> ## Update
>
> - **Days:** "14 today" · "13 tomorrow" · "16 Friday" · "15 2026.11.10" · "17 unplan" · "14 on due date" · "18 today" (follow up on the blocker today)
> - **Assign:** "assign 14 to alex@example.com" · "assign 16 to me" · "18 owner dana@example.com"
> - **Task status:** "12 done" · "14 in progress" · "16 cancel"
> - **Milestone status:** "M2 complete" · "M3 cancel"
> - **Blocker status:** "18 resolved" · "13 blocked on legal review" (adds a blocker)
> - "Show details for 14"
>
> A bare list of numbers requires clarification about the intended action.
>
> **Next project?** Reply "next" for Cloud Sync, "previous" to go back, or "finish" to skip to the plan recap.
>
> <!-- if: last_project -->
> **Ready to finalize today's plan?** Reply "yes" to see the recap, or keep updating.
> <!-- endif -->

---

## Notes

- **What you can do here.** Plan tasks (and blocker follow-ups) to days, assign tasks and blockers to people, and update the status of tasks, milestones and blockers. Structural edits (DoD wording, adding milestones, moving tasks between milestones) go to the project update screen.
- **One project per screen.** Stable order: projects with unplanned plannable work first. "next" / "previous" move between projects; "finish" jumps to the recap.
- **Milestone outline.** Every milestone is listed with its state. Milestones are addressed by label ("M2 complete"); labels are unique within the project on screen.
- **Plannable milestones.** The lowest incomplete milestone is always plannable. Other **in-progress** milestones are plannable too when the *include in-progress milestones* option is on ("include in-progress milestones" / "only M2" toggles it). Not-started milestones have no task table.
- **Status rules.** "Done" requires all DoD items checked and no open blockers; if not met, the screen says what's missing. Completing or cancelling a milestone requires all its tasks to be finished, or an explicit decision for each open task; cancelling never cascades.
- **Session numbering.** Row numbers continue from screen 1 (11 onward) and stay fixed for the whole session, across projects and refreshes. A number always means the same task or blocker.
- **Planned day** is the single active day for each task (Today, a date, or —). Choosing a new day moves it; "unplan" clears it. Due Date is never changed.
- **Blocked tasks** can still be planned; ⛔ is a warning, not a rule.
- **Changes apply immediately** after validation; each one is recorded in the decision log as a question and its resolution.
- **Hidden refs.** Each numbered row carries `<!-- ref: UUID -->` in the rendered markdown; omitted here for readability.
