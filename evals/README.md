# Daily Tasks evaluation

## Fast local Waza trigger checks

`evals/waza/skills/daily-tasks/` and `evals/waza/skills/daily-tasks-*/` mirror the six canonical skill
directories: the router, setup, capture, records, plan and check-in. Each Waza
suite has in-scope and out-of-scope prompts with the local `trigger`
grader. The mock executor avoids model calls, credentials and external services,
so these small suites are suitable for quick repeatable checks while editing
skill descriptions and routing language.
The grader's default threshold is 0.6: positive cases need a score of at least 0.6,
and negative cases must stay below it. Relevance scores are diagnostic, not a
standalone measure of end-to-end workflow quality.

Run a skill's trigger suite with the Waza CLI from the repository root:

```text
waza run evals/waza/skills/daily-tasks-plan
waza run evals/waza/skills/daily-tasks-capture
```

The [setup acceptance catalog](waza/skills/daily-tasks-setup/scenario-catalog.yaml)
documents setup behavior scenarios across personal and workspace scopes.
