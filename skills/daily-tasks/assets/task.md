---
id: TASK_UUID
type: task
record_version: 2
title: "TASK_TITLE"
document-maturity: draft
task-state: not-started
owner: "OWNER_EMAIL"
project_id: "PROJECT_UUID"
milestone_id: "MILESTONE_UUID"
created_at: "GMT_TIMESTAMP"
updated_at: "GMT_TIMESTAMP"
---
# M1-T1 — TASK_TITLE

> Provisional template — evaluate on a real task before accepting this format.

**Milestone:** [[MILESTONE_SLUG|MILESTONE_TITLE]] <!-- ref: MILESTONE_UUID -->

**Project:** [[../project-index|PROJECT_TITLE]] <!-- ref: PROJECT_UUID -->

## Requirements

Describe the work to complete and the concrete result to deliver. Explain why
it matters and any context the agent cannot discover from the supplied inputs.

## Definition of Done

- [ ] State an observable task acceptance criterion. <!-- id: TASK_CRITERION_UUID -->

These criteria belong to this task. Record satisfaction and evidence explicitly;
producing a file alone does not establish that the task is complete.

## Scope and constraints

- **Include:** The specific changes or deliverables this task covers.
- **Exclude:** Explicit boundaries that matter to execution.
- **Preserve:** Existing behavior, content or conventions that must be retained.
- **Authority:** State which actions are authorized: file edits, commits, pushes,
  opening a PR, or other external changes. Assignment alone does not authorize
  messages, deployment, merging or publication.

## Inputs

| Input | Location | Use |
| --- | --- | --- |
| Primary input | Exact file path, folder, repository URL or document link | What to read or modify. |
| Supporting input | Exact path or link, including sheet/tab/range or section if relevant | Which information to extract. |

Specify the repository/workspace root for relative paths, the relevant branch or
revision when required, and how to distinguish the authoritative input from older
copies. Identify required account access without placing credentials in this file.
Local input files live directly in the milestone's inputs/ folder. Link each actual
file here using its relative path, purpose and source. Do not create subfolders.

## References

| Reference | Location | Guidance |
| --- | --- | --- |
| Requirements | Exact document path or link and relevant section | The behavior or facts to satisfy. |
| Example or standard | Exact path or link | What to follow and what is illustrative. |

State precedence if references disagree. Read the destination's applicable
`AGENTS.md` and local instructions before making changes.

## Plugins and skills

| Plugin or skill | Required or optional | Use for |
| --- | --- | --- |
| Exact installed plugin/skill name | Required | The operation or workflow it must handle. |
| Exact installed plugin/skill name | Optional | A useful capability and an allowed fallback. |

Verify required capabilities are available before dependent work. If one is missing,
report the specific blocker and continue independent work. Do not silently substitute
another workflow for an explicitly required skill. Omit this section when none apply.

## Execution guidance

1. Inspect the inputs, applicable instructions and existing work.
2. Complete the specified work using the required references and capabilities.
3. Validate the result against the checks below.
4. Deliver to the specified destination and record the result.

Replace these steps with task-specific guidance where sequence or approach matters.
Leave routine implementation choices to the agent. Identify dependencies, assumptions
it may resolve independently, and decisions it must bring back to the owner.

## Output and delivery

- **Delivery mode:** Local artifact / repository change / pull request. Select the
  applicable mode and remove unused instructions.
- **Destination:** Exact files directly in the milestone's outputs/ folder.
- **Format:** File type, naming convention, required structure and template to use.
- **Existing output:** Specify whether to create, update or replace; preserve unrelated work.
- **Handoff:** Provide clickable output links, a concise account of changes, validation
  results, and any unresolved issues.

Keep working material within the project; disposable scratch belongs in its .temp/.
Inputs and outputs are flat holding areas, with no task subfolders or folder indexes.
Use descriptive filenames and resolve collisions without overwriting unrelated files.
An explicitly authorized external delivery has a link and receipt in this task;
keep the local deliverables in outputs/.

### Pull request delivery

- **Repository and working directory:** REPOSITORY_URL and WORKSPACE_ROOT.
- **Base branch:** BASE_BRANCH.
- **Branch:** Required branch name or permission to choose a descriptive name.
- **PR state:** Draft or ready for review, with the required title/body conventions.
- **Required checks:** Exact test/build/lint commands and any browser or manual checks.
- **Completion:** Push the task changes and open or update the PR; return its URL and
  check status. Do not merge or deploy unless separately authorized.

Omit this subsection for tasks that do not deliver a PR. If PR delivery is specified,
a local diff alone is incomplete; report any precise publication blocker.

## Verification

Explain how to verify this task's Definition of Done above. Link supporting evidence
from outputs/ and the relevant milestone outcome when helpful. Task and milestone
criteria remain independently owned; never copy milestone criteria as task criteria.

- Expected observable result, with a concrete example when useful.
- Exact command or inspection method and what a passing result means.
- Required evidence: test results, rendered artifact, screenshot or source citation.

## Depends on

- [[DEPENDENCY_TASK_SLUG|DEPENDENCY_TASK_TITLE]] <!-- ref: DEPENDENCY_TASK_UUID -->

## Required by

- [[DEPENDENT_TASK_SLUG|DEPENDENT_TASK_TITLE]] <!-- ref: DEPENDENT_TASK_UUID -->

## Blocked by

- [[../blockers/bBLOCKER_NUMBER-BLOCKER_SLUG|BLOCKER_TITLE]] <!-- ref: BLOCKER_UUID -->

## Decisions needed

- **Question:** The unresolved choice that affects execution.
  - **Decision owner:** Who can resolve it.
  - **Can continue:** Which independent work may proceed while awaiting the answer.

## Result

Complete after execution: link the delivered artifact or PR, summarize verification,
and record remaining limitations or blockers. Do not mark the task complete when
required delivery or checks remain unfinished.

<!-- Formatting example for <project>/m1-milestone-name/t1-task-name.md.
The draft maturity and provisional notice describe this template. When creating
an actual task, omit the template notice and choose its document maturity from
the actual review/acceptance of that task's instructions, not this template's state.
Replace all placeholders with accepted facts; omit unused sections and sample relationship rows.
Do not create dependencies, blockers, assignments or authority from example text.
Use optional scalar assignee/target_date metadata only when explicitly supplied.
Record relationships reciprocally using the record conventions. Keep detailed
instructions here; the project index remains a concise summary. -->
