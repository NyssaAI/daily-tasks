# Evaluation Receipts: `daily-tasks`

> [!IMPORTANT] Scope Directive
> Records canonical verification receipts, Waza suite inventory, and multi-host evaluation status for `daily-tasks` release readiness. It does NOT define evaluation scenarios (owned by `waza/skills/daily-tasks/`).

**Last Verified**: 2026-11-04  
**Version**: 0.10.0  
**Topology**: Encapsulated Facade (`skills/daily-tasks/SKILL.md` + 5 internal workflows)  
**Status**: Local Verification Passing / Native Host Matrix Pending Live Run  

---

## Verification Summary

| Gate | Target | Status | Details |
| :--- | :--- | :--- | :--- |
| **Canonical Skill & Link Validator** | [`scripts/validate.py`](../scripts/validate.py) | **PASS** | Validated 1 skill, 5 workflows, 8 references, relative links, path hygiene, and version parity (`0.10.0`) |
| **Host Package Assembler** | [`scripts/assemble.py`](../scripts/assemble.py) | **PASS** | `1234` generated files match canonical source across `portable`, `antigravity`, `cowork`, and `hermes` |
| **Cross-Plugin Standards Check** | `skills/daily-tasks/` | **PASS** | All Scope Directives, `## Verification` sections, frontmatter, and `#anchor` links verified |
| **Waza Trigger Suite** | [`waza/skills/daily-tasks/eval.yaml`](waza/skills/daily-tasks/eval.yaml) | **PASS (Defined)** | 10 positive workflow triggers + 7 challenging near-neighbor negative boundary cases |
| **Behavioral Grader & Fixture** | [`waza/skills/daily-tasks/behavior.yaml`](waza/skills/daily-tasks/behavior.yaml) | **PASS (Ported)** | `personal-only-first-setup` task, synthetic-home fixture, and [`validate-personal-only.py`](waza/skills/daily-tasks/graders/validate-personal-only.py) grader |
| **Unit & Integration Test Suite** | `test/unit/daily_tasks/` | **PASS** | 330 Python unit & MCP session integration tests passing |

---

## Waza Suite Inventory (`evals/waza/skills/daily-tasks/`)

### Positive Trigger Cases (10)
- [`in-scope.yaml`](waza/skills/daily-tasks/tasks/in-scope.yaml): End-to-end setup, candidate capture, and daily planning routing.
- [`setup-in-scope.yaml`](waza/skills/daily-tasks/tasks/setup-in-scope.yaml): First-use identity, timezone, and storage binding setup.
- [`setup-personal-only-in-scope.yaml`](waza/skills/daily-tasks/tasks/setup-personal-only-in-scope.yaml): Personal-only preference setup without workspace bindings.
- [`setup-change-preference-in-scope.yaml`](waza/skills/daily-tasks/tasks/setup-change-preference-in-scope.yaml): Explicit timezone preference update.
- [`setup-project-setup-not-done-in-scope.yaml`](waza/skills/daily-tasks/tasks/setup-project-setup-not-done-in-scope.yaml): Prerequisite setup trigger when workspace profile is missing.
- [`capture-in-scope.yaml`](waza/skills/daily-tasks/tasks/capture-in-scope.yaml): Candidate commitment extraction and deduplication from meeting notes.
- [`records-in-scope.yaml`](waza/skills/daily-tasks/tasks/records-in-scope.yaml): Direct named task creation under a milestone with embedded DoD criteria.
- [`records-fix-malformed-in-scope.yaml`](waza/skills/daily-tasks/tasks/records-fix-malformed-in-scope.yaml): Surgical frontmatter and state repair of a malformed task file.
- [`plan-in-scope.yaml`](waza/skills/daily-tasks/tasks/plan-in-scope.yaml): Local-day task selection and review screen presentation.
- [`checkin-in-scope.yaml`](waza/skills/daily-tasks/tasks/checkin-in-scope.yaml): Resuming a check-in, reconciling manual plan edits, and opening today's plan.

### Near-Neighbor Negative Boundary Cases (7)
- [`out-of-scope.yaml`](waza/skills/daily-tasks/tasks/out-of-scope.yaml): Calendar time-slot blocking and duration estimation (`9:00 AM`–`5:00 PM` 30-minute blocks).
- [`capture-out-of-scope.yaml`](waza/skills/daily-tasks/tasks/capture-out-of-scope.yaml): Filing reference notes into a PARA vault's `3-resources` folder and repairing MOC links (`para-vault` boundary).
- [`checkin-out-of-scope.yaml`](waza/skills/daily-tasks/tasks/checkin-out-of-scope.yaml): Babysitting an open GitHub pull request and resolving CI checks (`ce-babysit-pr` boundary).
- [`plan-out-of-scope.yaml`](waza/skills/daily-tasks/tasks/plan-out-of-scope.yaml): Sequencing a Q4 product feature roadmap and fitting 25-minute Pomodoro timer intervals (`plan-product` / time-fitting boundary).
- [`records-out-of-scope.yaml`](waza/skills/daily-tasks/tasks/records-out-of-scope.yaml): Safely renaming a repository directory and repairing broken file paths (`manage-file-operations` boundary).
- [`setup-out-of-scope.yaml`](waza/skills/daily-tasks/tasks/setup-out-of-scope.yaml): Learning a personal writing style and updating a voice profile from sample emails (`write-like-me` boundary).
- [`setup-general-timezone-out-of-scope.yaml`](waza/skills/daily-tasks/tasks/setup-general-timezone-out-of-scope.yaml): Booking a recurring cross-timezone calendar invite across `America/Chicago` and `Europe/London`.

### Behavioral Scenarios
- [`personal-only.yaml`](waza/skills/daily-tasks/tasks/behavior/personal-only.yaml): Isolated synthetic-home execution verifying Schema Version 2 profile creation and strict absence of workspace artifacts via [`validate-personal-only.py`](waza/skills/daily-tasks/graders/validate-personal-only.py).
- Full 29-scenario specification tracked in [`scenario-catalog.yaml`](waza/skills/daily-tasks/scenario-catalog.yaml).
