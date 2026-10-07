# Daily Tasks

Public NyssaAI plugin. Maintain canonical instructions under `skills/`; host files
are thin generated manifests. This is a skill collection, not an agent persona.
Never add automatic scheduling, time fitting, or implicit acceptance.

JavaScript is ESM, Node >=22, dependency-free unless a concrete need requires one.
Feature modules live under `lib/<feature>/`; CLI under `bin/`. No generic utils.
Use `node --test` for behavior and integration checks. Keep scratch in `.temp/`.
Public requirements live in `docs/`; never include personal records or credentials.
Regenerate manifests/artifacts with `node scripts/assemble.mjs write`, then check.
Do not claim host activation from packaging or direct CLI tests.

The log is script-only. Other Markdown writes belong to skills; integrity code
validates, compares and proposes changes without owning the full workflow.
Keep resolved config, vault and projects roots independent of cwd. Reuse existing
settings and the established `.nyssaai` state convention before asking for missing scope.
