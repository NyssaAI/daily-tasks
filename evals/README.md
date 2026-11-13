# Daily Tasks evaluation

## Fast local Waza trigger checks

`evals/waza/skills/daily-tasks/` evaluates the encapsulated `daily-tasks` entry skill ([`skills/daily-tasks/SKILL.md`](../skills/daily-tasks/SKILL.md)), which routes across the five workflows (`setup`, `capture`, `records`, `plan`, and `checkin`). The Waza trigger suite ([`eval.yaml`](waza/skills/daily-tasks/eval.yaml)) includes **18** single-`TestCase` tasks (**11** positive in-scope prompts and **7** near-neighbor out-of-scope boundary prompts) graded offline with the `trigger` grader (`executor: mock`):

### Positive trigger tasks (11)

- [`in-scope.yaml`](waza/skills/daily-tasks/tasks/in-scope.yaml): End-to-end setup, candidate capture, and daily planning routing.
- [`setup-in-scope.yaml`](waza/skills/daily-tasks/tasks/setup-in-scope.yaml): First-use identity, timezone, and storage binding setup.
- [`setup-personal-only-in-scope.yaml`](waza/skills/daily-tasks/tasks/setup-personal-only-in-scope.yaml): Personal-only preference setup without workspace bindings.
- [`setup-change-preference-in-scope.yaml`](waza/skills/daily-tasks/tasks/setup-change-preference-in-scope.yaml): Explicit timezone preference update.
- [`setup-project-setup-not-done-in-scope.yaml`](waza/skills/daily-tasks/tasks/setup-project-setup-not-done-in-scope.yaml): Prerequisite setup trigger when workspace profile is missing.
- [`setup-harness-aware-mcp-in-scope.yaml`](waza/skills/daily-tasks/tasks/setup-harness-aware-mcp-in-scope.yaml): Harness-aware MCP registration and Schema v2 profile prerequisite setup routing.
- [`capture-in-scope.yaml`](waza/skills/daily-tasks/tasks/capture-in-scope.yaml): Candidate commitment extraction and deduplication from meeting notes.
- [`records-in-scope.yaml`](waza/skills/daily-tasks/tasks/records-in-scope.yaml): Direct named task creation under a milestone with embedded DoD criteria.
- [`records-fix-malformed-in-scope.yaml`](waza/skills/daily-tasks/tasks/records-fix-malformed-in-scope.yaml): Surgical frontmatter and state repair of a malformed task file.
- [`plan-in-scope.yaml`](waza/skills/daily-tasks/tasks/plan-in-scope.yaml): Local-day task selection and review screen presentation.
- [`checkin-in-scope.yaml`](waza/skills/daily-tasks/tasks/checkin-in-scope.yaml): Resuming a check-in, reconciling manual plan edits, and opening today's plan.

### Near-neighbor negative boundary tasks (7)

- [`out-of-scope.yaml`](waza/skills/daily-tasks/tasks/out-of-scope.yaml): Calendar time-slot blocking and duration estimation (`9:00 AM`–`5:00 PM` 30-minute blocks).
- [`capture-out-of-scope.yaml`](waza/skills/daily-tasks/tasks/capture-out-of-scope.yaml): Filing reference notes into a PARA vault's `3-resources` folder and repairing MOC links (`para-vault` boundary).
- [`checkin-out-of-scope.yaml`](waza/skills/daily-tasks/tasks/checkin-out-of-scope.yaml): Babysitting an open GitHub pull request and resolving CI checks (`ce-babysit-pr` boundary).
- [`plan-out-of-scope.yaml`](waza/skills/daily-tasks/tasks/plan-out-of-scope.yaml): Sequencing a Q4 product feature roadmap and fitting 25-minute Pomodoro timer intervals (`plan-product` / time-fitting boundary).
- [`records-out-of-scope.yaml`](waza/skills/daily-tasks/tasks/records-out-of-scope.yaml): Safely renaming a repository directory and repairing broken file paths (`manage-file-operations` boundary).
- [`setup-out-of-scope.yaml`](waza/skills/daily-tasks/tasks/setup-out-of-scope.yaml): Learning a personal writing style and updating a voice profile from sample emails (`write-like-me` boundary).
- [`setup-general-timezone-out-of-scope.yaml`](waza/skills/daily-tasks/tasks/setup-general-timezone-out-of-scope.yaml): Booking a recurring cross-timezone calendar invite across `America/Chicago` and `Europe/London`.

Run preflight and the trigger suite with the Waza CLI from the repository root:

```text
waza preflight --no-update-check evals/waza/skills/daily-tasks/eval.yaml
waza preflight --no-update-check evals/waza/skills/daily-tasks/behavior.yaml
waza run --no-update-check evals/waza/skills/daily-tasks/eval.yaml
```

## Isolated behavioral setup checks

[`behavior.yaml`](waza/skills/daily-tasks/behavior.yaml) runs **1** isolated personal-only setup task ([`tasks/behavior/personal-only.yaml`](waza/skills/daily-tasks/tasks/behavior/personal-only.yaml)) against [`fixtures/personal-only/synthetic-home/`](waza/skills/daily-tasks/fixtures/personal-only/synthetic-home/README.md) and grades the resulting `~/.nyssa-ai/daily-tasks/config.json` and directory tree deterministically with [`graders/validate-personal-only.py`](waza/skills/daily-tasks/graders/validate-personal-only.py). The [setup acceptance catalog](waza/skills/daily-tasks/scenario-catalog.yaml) documents the 29 setup behavior scenarios across personal and vault scopes.

## Coverage matrix and deterministic reporting

[`matrix.json`](matrix.json) declares the 11 target host rows (`schema: 1`, `version: "0.11.3"`, `suite_revision: "0.11.3"`) across required and optional harnesses. [`report.py`](report.py) computes the CRLF-normalized `Candidate SHA-256`, validates any locally retained `.temp/evals/evidence/` receipts, and renders [`LATEST.md`](LATEST.md):

```text
uv run python evals/report.py generate
uv run python evals/report.py check
uv run python evals/report.py release
uv run python evals/report.py summary
```

- `generate` rewrites [`LATEST.md`](LATEST.md) from [`matrix.json`](matrix.json) and verified receipts under `.temp/evals/evidence/` (rendering run IDs as inline code rather than broken relative links).
- `check` verifies [`LATEST.md`](LATEST.md) matches the current candidate hash and coverage matrix without mutating files (enforced in CI).
- `release` exits non-zero whenever any `required: true` row in [`matrix.json`](matrix.json) lacks a current, independently reviewed `Pass` receipt.
- `summary` (and `summary --no-code-tests` or `hash`) emits deterministic JSON counts across both `eval.yaml` (18 trigger tasks) and `behavior.yaml` (1 behavioral task), the 11-row host matrix, and `pytest`.

Per-host native activation must be verified in an isolated host environment outside `repo_root` (`uv run python scripts/assemble.py write --output-dir <isolated-env>`); never self-load `.agents/` or `.hermes/` inside `repo_root`.
