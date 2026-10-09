# Daily Tasks activation cases

Human-readable U1 specification, version 1. These cases define later natural
activation runs; no run or host acceptance is established by this document.
Evaluate the workflow selected and justified handoffs, not how many skills load.
Keep task prompts separate from expected criteria; provide only the prompt and
ordinary fixture context to the agent, never this document's route or criteria.
Natural activation runs must leave forced activation and scoring disabled.

## Fixture context

Use synthetic records only. Except A02, provide an established vault binding,
existing profile and readable records for project Website and milestone Launch.
The profile identifies Casey (casey@example.test), with America/Chicago timezone.
Launch contains accepted tasks Draft landing copy and Review launch checklist.
Draft landing copy is not started; Review launch checklist has satisfied DoD and
no preventing blockers. Alex's known assignee email is alex@example.test.
Provide no unrelated pending operations or conflicts.

For A02, use a fresh bound vault without a profile. For A05 and A06, retain an
earlier local-day plan with unfinished selected work. A06 and A14 include a manual
new unchecked row, Prepare launch announcement, with no accepted task identity.
For A10 and A14, present an active saved planning screen whose stable mapping is
row 2 = Draft landing copy and row 4 = Review launch checklist. Record the same
vault binding and local date as the current session.

## Task prompts

| ID | User prompt |
| --- | --- |
| A01 | Help me manage my Website work: review where things stand, then let me choose what to work on today. |
| A02 | Set up Daily Tasks for this vault. I'm Casey, casey@example.test. |
| A03 | Pull out the action items from this meeting note: Alex said, "Casey, please prepare a launch announcement." |
| A04 | Reassign Draft landing copy to Alex. |
| A05 | Plan my day. |
| A06 | Check in on my Website work; I edited the plan's checkboxes since our last session. |
| A07 | Create a task named Test launch links under Website's Launch milestone. Requirements: check every public launch link. Done when each link reaches its intended page. |
| A08 | Create two tasks under Website's Launch milestone: Check footer links, done when every footer link reaches its intended page; Check header links, done when every header link reaches its intended page. Both require checking the public launch page. |
| A09 | Help me plan the structure of an essay about urban trees. |
| A10 | 2, 4 |
| A11 | Mark Review launch checklist done, then add Draft landing copy to today. |
| A12 | Find possible work in this note: "I promised I'd prepare a launch announcement." |
| A13 | Explain how JavaScript promises work. |
| A14 | 4 is done. Also review the new launch announcement checkbox I added. |

## Expected criteria

| ID | Expected workflow and observable boundary |
| --- | --- |
| A01 | Router composes Check-in and Plan as needed: reconcile current progress before offering explicit day selections. Discovery alone does not select work. |
| A02 | Setup resolves the bound vault, asks only for missing preference scope/data, and preserves the independent vault/state binding. No request for internal storage paths or separate state-initialization approval. |
| A03 | Capture extracts and deduplicates the quoted third-party request as a candidate. No accepted task is created without Casey's affirmative acceptance. |
| A04 | Records updates assignee to Alex, preserves Casey as owner and does not start execution or select the task for today. |
| A05 | Plan resolves existing configuration, reconciles edits and recovers pending operations as needed, verifies rollover and offers explicit selections. It does not fit work into time or ask for execution ordering. |
| A06 | Check-in reconciles edits, validates completion claims, treats the new unidentified checkbox as a candidate, and handles today's plan/carry-forward under the existing protocol. |
| A07 | Records creates the named accepted task, using Capture's acceptance contract if needed. The user's creation instruction supplies acceptance; no repeated acceptance prompt. Ask only for material missing details and verify saved effects. |
| A08 | Records creates only the two named tasks without asking to accept the named batch again. No additional agent-proposed work is accepted. |
| A09 | No Daily Tasks workflow: ordinary essay-structure planning does not establish a personal task-management request. No plugin records or profile are created. |
| A10 | Plan/response conventions retain the active mapping and ask what action is intended. Bare numbers cause no selection, lifecycle change or acceptance. |
| A11 | Records validates/applies completion and required parent effects, then Plan selects Draft landing copy for today without starting it. The handoff preserves ownership, logging and recovery requirements. |
| A12 | Capture treats the source promise as possible work, not acceptance. No canonical task is created solely from the promise. |
| A13 | No Daily Tasks workflow: a programming explanation about promises is unrelated. No plugin writes occur. |
| A14 | Check-in hands explicit completion to Records and the unidentified new row to Capture. It processes the clear completion independently and does not accept the new candidate implicitly. |

## Direct child activation

Repeat A02, A03, A04, A05 and A06 with only the corresponding child skill as the
entry skill, without preloading the router. Repeat A07 with Records as entry and
with Capture as entry. These are separate dependency checks, not natural-activation
results. Each child must reach its required sibling/shared contracts, reuse existing
configuration where present and preserve the same acceptance, ownership, logging,
recovery and selection boundaries. Direct entry must not introduce redundant setup
or acceptance questions.

## Recording evidence

Record source identity, fixture version, actual agent/model, run ID and each case's
observed route/handoff with criterion results and unresolved limitations. Distinguish
description review, natural activation, direct-child execution and native-host
acceptance. Missing execution infrastructure remains Not run; package validation or
direct CLI execution cannot establish host activation. Keep prompts free of route
names and answer hints when translating these cases into executable scenarios.
