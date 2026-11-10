# Daily Tasks Ubiquitous Language Glossary

Authoritative bounded-context lexicon for `daily-tasks` (`REPO-GOVERNANCE`, `ARCH-NAME`). Detailed invariants and lifecycle state machines live in [`docs/CONCEPTS.md`](CONCEPTS.md) and versioned JSON contracts in [`docs/specs/`](specs/).

| **Canonical Term** | `CodeSymbol` | Banned Synonyms | Definition |
| :--- | :--- | :--- | :--- |
| **Workspace** | `ServerSettings`, `WorkspaceReader`, `WorkspaceSnapshot` | `VaultRepo`, `ProjectWorkspace`, `RepoDir` | User-owned directory root containing `projects/`, `daily-plans/`, and `.nyssa-ai/daily-tasks/`. |
| **Project** | `Project`, `ProjectState` | `Initiative`, `Epic` | Accepted outcome-oriented effort (`projects/YYYY.MM.DD-<slug>/project-index.md`). |
| **Milestone** | `Milestone`, `MilestoneState` | `Sprint`, `Phase` | Concrete checkpoint inside a `Project` (`mN-<slug>/mN-<slug>.md`). |
| **Task** | `Task`, `TaskState`, `DodItem` | `Todo`, `Ticket`, `Issue` | Accepted unit of work (`tN-<slug>.md`) with stable `DodItem` checklist IDs. |
| **External Blocker** | `Blocker`, `BlockerState` | `Impediment`, `DependencyIssue` | Condition outside direct execution control (`blockers/bN-<slug>.md`) blocking tasks or milestones. |
| **Daily Plan** | `DailyPlan`, `DailyPlanDocument` | `Schedule`, `TimeboxPlan`, `Agenda` | User's explicit selection of accepted tasks for a local calendar date (`daily-plans/YYYY.MM.DD-daily-plan.md`), never time-fitted. |
| **Planning Session** | `PlanningSession`, `PlanningSessionPort`, `PlanningTools`, `PlanningToolsDispatcher` | `PlanningToolsProtocol`, `CheckinWizard`, `SessionManager` | Stateful 3-screen deterministic adjudication workflow (`s1` Triage -> `s2` Plan -> `s3` Confirm) over MCP. |
| **Suggestion** | `Suggestion`, `Suggestions`, `SuggestionKind` | `AutoUpdate`, `DraftMutation` | Deterministic candidate state change matched from communication messages, requiring explicit user verdict (`accept`, `modify`, `reject`, `defer`). |
| **Record Change** | `RecordChange`, `LocalFileStore`, `MarkdownFileStore` | `Patch`, `FileMutation` | Optimistically concurrency-checked (`expected_hash`) surgical edit staged in memory and persisted only on `confirm_plan(confirmed=True)`. |
| **Decision Log** | `DecisionLog`, `DecisionLogEntry`, `DecisionLogger` | `AuditTrail`, `HistoryLog` | Append-only record of user verdicts and planning operations in `.nyssa-ai/daily-tasks/decision-log.json`. |
| **Fetch Cursor** | `FetchCursor`, `FetchCursors`, `CursorStore` | `SyncToken`, `WatermarkFile` | Per-source high-water mark (`since`, `last_external_id`) persisted in `.nyssa-ai/daily-tasks/fetch-cursors.json` after confirmed sessions. |
| **Secret String** | `SecretString`, `SecretResolver`, `SecretCaptureService` | `PlainToken`, `RawSecret` | Redacting in-memory credential wrapper that reveals plaintext only via `.reveal()` at outbound I/O boundaries. |
