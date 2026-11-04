# Product Feature Progress

| Feature Group | Complete / Total | % Complete |
| --- | --- | --- |
| Group 00: Foundation | 3 / 4 | 75% |
| Group 01: Commitment Capture & Record Management | 2 / 2 | 100% |
| Group 02: Interactive Daily Planning Session | 3 / 3 | 100% |
| Group 03: Assistant Host Integration & Distribution | 2 / 2 | 100% |
| **Overall** | **10 / 11** | **91%** |

---

## How to Use This Feature Inventory

This document catalogs product capabilities in non-technical, user-focused language, organized by functional capability groups.

| Numbering Pattern | Canonical Name | Segment Definitions | Path / Location |
| :--- | :--- | :--- | :--- |
| **`F-gg.nn`**<br>*(e.g. `F-01.02`)* | **Feature ID** | • **`gg` = Feature Group** (`00`–`99`): Cohesive functional area clustering related features (`00` = Foundation).<br>• **`nn` = Feature Number** (`01`–`99`): Sequential feature within that Feature Group. | `docs/features/f-gg.nn/feature.md` |
| **`UC-gg.nn.uu`**<br>*(e.g. `UC-01.02.01`)* | **Use Case ID** | • **`gg` = Feature Group** (`00`–`99`): Inherited from parent Feature.<br>• **`nn` = Feature Number** (`01`–`99`): Inherited from parent Feature.<br>• **`uu` = Use Case Number** (`01`–`99`): Sequential actor workflow within `F-gg.nn`. | `docs/features/f-gg.nn/uc-gg.nn.uu-short-slug.md` |
| **`R-pp.ss`**<br>*(e.g. `R-01.03`)* | **Roadmap Step ID** | • **`pp` = Phase** (`00`–`99` or `01`–`99`): Technical delivery stage in build order.<br>• **`ss` = Step** (`01`–`99`): Ordered unit of delivery work within Phase `pp` that completes/verifies target `UC-gg.nn.uu`s (or `F-gg.nn` fallback). | `docs/roadmap.md` |

* **User-Focused Language:** Describe features in plain, use-case language explaining what users can accomplish—not internal file paths or implementation details.
* **Checklist Summary:** Keep `## Feature Checklist Summary` scannable with `- [ ] F-gg.nn: Feature Title` only (no links needed, as `F-gg.nn` maps directly to `features/f-gg.nn/feature.md`).
* **Status:** Mark an item complete (`[x]`) only when the capability is implemented, documented, and verified.

---

## Feature Checklist Summary

### Group 00: Foundation

- [x] F-00.01: Workspace, Identity & Template Setup
- [x] F-00.02: Canonical Work Record Storage & Surgical Updates
- [x] F-00.03: Credential Privacy & Read-Only Communication Connections
- [ ] F-00.04: Existing Assistant Connection Discovery & Bounded Lookback Ingestion

### Group 01: Commitment Capture & Record Management

- [x] F-01.01: Candidate Work Capture & Deduplication
- [x] F-01.02: Project, Milestone, Task & Blocker Lifecycle Management

### Group 02: Interactive Daily Planning Session

- [x] F-02.01: Communication Correlation & Update Suggestions
- [x] F-02.02: Three-Screen Daily Planning & Day Assignment
- [x] F-02.03: Anytime Check-In & Manual Edit Reconciliation

### Group 03: Assistant Host Integration & Distribution

- [x] F-03.01: Workflow Skill Routing & Host Bundle Distribution
- [x] F-03.02: Planning Session Tool Service & Syndication

---

## Feature Inventory

### Group 00: Foundation

**F-00.01: Workspace, Identity & Template Setup**  
Configure personal identity, local timezone, daily priorities, workspace storage locations, and customizable document templates with controlled template update preferences.  
[Feature Guide: Workspace, Identity & Template Setup](features/f-00.01/feature.md)

**F-00.02: Canonical Work Record Storage & Surgical Updates**  
Read and update editable project, milestone, task, blocker, and daily plan documents while preserving user-authored notes, comments, and layout formatting intact.  
[Feature Guide: Canonical Work Record Storage & Surgical Updates](features/f-00.02/feature.md)

**F-00.03: Credential Privacy & Read-Only Communication Connections**  
Connect to email and team chat accounts in strictly read-only mode, keeping credentials protected in memory and tracking incremental message checkpoints so messages are never fetched twice.  
[Feature Guide: Credential Privacy & Read-Only Communication Connections](features/f-00.03/feature.md)

**F-00.04: Existing Assistant Connection Discovery & Bounded Lookback Ingestion**  
Detect email and chat connections already available in the user's AI assistant environment during setup, let the user choose which connections to use and configure their initial lookback window (defaulting to no more than 7 days on the first pull), and process messages from existing connections using the exact same incremental checkpoints and suggestion workflows as built-in connections.  
[Feature Guide: Existing Assistant Connection Discovery & Bounded Lookback Ingestion](features/f-00.04/feature.md)

### Group 01: Commitment Capture & Record Management

**F-01.01: Candidate Work Capture & Deduplication**  
Extract possible tasks, milestones, and projects from notes, messages, or conversations, check them against existing work for duplicates, and hold them for explicit individual or batch acceptance.  
[Feature Guide: Candidate Work Capture & Deduplication](features/f-01.01/feature.md)

**F-01.02: Project, Milestone, Task & Blocker Lifecycle Management**  
Create accepted projects, milestones, tasks, and external blockers; manage Definitions of Done, ownership, delegation, target dates, and dependencies; and enforce completion rules before closing work.  
[Feature Guide: Project, Milestone, Task & Blocker Lifecycle Management](features/f-01.02/feature.md)

### Group 02: Interactive Daily Planning Session

**F-02.01: Communication Correlation & Update Suggestions**  
Link unread emails and chat messages to matching projects, tasks, and blockers, detect progress or blocker signals, and propose numbered update suggestions citing the source message.  
[Feature Guide: Communication Correlation & Update Suggestions](features/f-02.01/feature.md)

**F-02.02: Three-Screen Daily Planning & Day Assignment**  
Guide the user through reviewing today's carried-forward work and message suggestions (Screen 1), assigning open project tasks and blocker follow-ups to specific days (Screen 2), and confirming the final daily plan (Screen 3) with full decision logging.  
[Feature Guide: Three-Screen Daily Planning & Day Assignment](features/f-02.02/feature.md)

**F-02.03: Anytime Check-In & Manual Edit Reconciliation**  
Run or resume a check-in at any time of day to reconcile manual document edits, record progress updates, resolve state conflicts, and carry unfinished work forward into today's plan.  
[Feature Guide: Anytime Check-In & Manual Edit Reconciliation](features/f-02.03/feature.md)

### Group 03: Assistant Host Integration & Distribution

**F-03.01: Workflow Skill Routing & Host Bundle Distribution**  
Route user requests to the appropriate Daily Tasks workflow skill and package ready-to-install skill bundles across supported AI assistant environments.  
[Feature Guide: Workflow Skill Routing & Host Bundle Distribution](features/f-03.01/feature.md)

**F-03.02: Planning Session Tool Service & Syndication**  
Expose the deterministic daily planning session to AI assistant hosts as a standard tool service with clean diagnostic logging, end-to-end verification, and project status syndication.  
[Feature Guide: Planning Session Tool Service & Syndication](features/f-03.02/feature.md)
