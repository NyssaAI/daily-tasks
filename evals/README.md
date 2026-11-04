# Daily Tasks evaluation

## Fast local Waza trigger checks

`evals/waza/skills/daily-tasks/` evaluates the encapsulated `daily-tasks` entry skill ([`skills/daily-tasks/SKILL.md`](../skills/daily-tasks/SKILL.md)), which routes across the five workflows (`setup`, `capture`, `records`, `plan`, and `checkin`). The Waza trigger suite ([`eval.yaml`](waza/skills/daily-tasks/eval.yaml)) includes 10 positive in-scope prompts and 7 near-neighbor out-of-scope boundary prompts graded with the local `trigger` grader (`executor: mock`).

Run the skill's trigger suite with the Waza CLI from the repository root:

```text
waza run evals/waza/skills/daily-tasks/eval.yaml
```

## Isolated behavioral setup checks

[`behavior.yaml`](waza/skills/daily-tasks/behavior.yaml) runs the isolated personal-only setup scenario ([`tasks/behavior/personal-only.yaml`](waza/skills/daily-tasks/tasks/behavior/personal-only.yaml)) against [`fixtures/personal-only/synthetic-home/`](waza/skills/daily-tasks/fixtures/personal-only/synthetic-home/README.md) and grades the resulting profile and directory tree deterministically with [`graders/validate-personal-only.py`](waza/skills/daily-tasks/graders/validate-personal-only.py).

The [setup acceptance catalog](waza/skills/daily-tasks/scenario-catalog.yaml) documents the 29 setup behavior scenarios across personal and workspace scopes, and [`LATEST.md`](LATEST.md) records the current verification status and evaluation receipts.
