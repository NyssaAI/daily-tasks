# Daily Tasks

Public NyssaAI plugin. Maintain canonical instructions under `skills/`; host files
are thin generated manifests. This is a skill collection, not an agent persona.
Never add time fitting, or implicit acceptance.

JavaScript is ESM, Node >=22, dependency-free unless a concrete need requires one.
Feature modules live under `src/core/<feature>/`; CLI entrypoints under `src/cli/`;
host adapters under `src/adapters/`. Use Node subpath imports (`#core/*`, `#cli/*`, `#adapters/*`).
Evaluation results follow the daily standard (`evals/results/YYYY.MM.DD-*`). No generic utils.
Use `node --test` for behavior and integration checks. Keep scratch in `.temp/`.

Python is allowed (>=3.12, managed with `uv` via `pyproject.toml`). Python code lives
under `src/daily_tasks/` and is tested with `pytest`. Python dependencies are limited to
`lang*` packages (e.g. `langchain-*`, `langgraph`) and `nyssa-ai` packages, plus others
only when a concrete need requires one.
Public behavior is documented in `README.md` and `skills/`; never include personal records or credentials.
Regenerate manifests/artifacts with `node scripts/assemble.mjs write`, then check.
Do not claim host activation from packaging or direct CLI tests.

The log is script-only. Other Markdown writes belong to skills, except for the
deterministic Daily Tasks planning session MCP server whose LocalFileStore is
authorized to apply validated record changes and daily plans exclusively following
explicit user adjudication; integrity code validates, compares and proposes changes
without owning the full workflow.
Keep resolved config, vault and projects roots independent of cwd. Reuse existing
settings before asking for missing scope. User and project configuration and
operating state use canonical `.nyssa-ai/daily-tasks/`; preserve accepted explicit paths.

# Development standards (python)

Read `.nyssa-ai/dev-standards/python/rules/repo-standards.md`,
`.nyssa-ai/dev-standards/python/rules/architecture-standards.md` and
`.nyssa-ai/dev-standards/python/rules/standards.md` before changing owned python code or repository layout.
The pinned source revision, owned roots and local commands are recorded in
`.nyssa-ai/dev-standards/python.json`. Repository requirements and explicit user instructions take
precedence; record the scope and reason of an exception in the change description.

Read relevant examples when a design choice needs one. For operational boundaries, also read
`.nyssa-ai/dev-standards/python/references/logging.md`. For tests and fixtures, read
`.nyssa-ai/dev-standards/python/references/testing.md`. Apply relevant entries of
`.nyssa-ai/dev-standards/python/references/code-smells.md` with source evidence and counterexamples.

Run applicable build/typecheck, unit and use-case commands locally. Unit tests must work without Docker.
A requested infrastructure test requires Docker; report missing prerequisites as blocked,
never as a pass. Use the structural checker as local feedback and report unsupported coverage
separately from rule violations. A green checker does not establish complete conformance.
Do not add CI wiring, hooks or automatic standards execution.

Validate adoption with:

```text
python .nyssa-ai/dev-standards/python/scripts/check_adoption.py .
```

Update the pinned local bundle from the installed `dev-standards` plugin with:

```text
python .nyssa-ai/dev-standards/python/scripts/check_adoption.py . --sync
```

Execute the configured local build and unit commands plus the structural checks with `--run`.
Add `--use-case` to run the configured infrastructure suite explicitly. Review command definitions
before executing them; they are owned by this repository.

# Development standards (typescript)

Read `.nyssa-ai/dev-standards/typescript/rules/repo-standards.md`,
`.nyssa-ai/dev-standards/typescript/rules/architecture-standards.md` and
`.nyssa-ai/dev-standards/typescript/rules/standards.md` before changing owned typescript code or repository layout.
The pinned source revision, owned roots and local commands are recorded in
`.nyssa-ai/dev-standards/typescript.json`. Repository requirements and explicit user instructions take
precedence; record the scope and reason of an exception in the change description.

Read relevant examples when a design choice needs one. For operational boundaries, also read
`.nyssa-ai/dev-standards/typescript/references/logging.md`. For tests and fixtures, read
`.nyssa-ai/dev-standards/typescript/references/testing.md`. Apply relevant entries of
`.nyssa-ai/dev-standards/typescript/references/code-smells.md` with source evidence and counterexamples.

Run applicable build, unit and use-case commands locally. Unit tests must work without Docker.
A requested infrastructure test requires Docker; report missing prerequisites as blocked,
never as a pass. Use the structural checker as local feedback and report unsupported coverage
separately from rule violations. A green checker does not establish complete conformance.
Do not add CI wiring, hooks or automatic standards execution.

Validate adoption with:

```text
python .nyssa-ai/dev-standards/typescript/scripts/check_adoption.py .
```

Update the pinned local bundle from the installed `dev-standards` plugin with:

```text
python .nyssa-ai/dev-standards/typescript/scripts/check_adoption.py . --sync
```

Execute the configured local build and unit commands plus the structural checks with `--run`.
Add `--use-case` to run the configured infrastructure suite explicitly. Review command definitions
before executing them; they are owned by this repository.
