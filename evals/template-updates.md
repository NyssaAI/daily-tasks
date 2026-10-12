# Template update native-host evaluation (template-updates-v1)

This is a separate host scenario, not an upgrade of historical workflow-v4
receipts. The fixture initializer creates starting records only. The verifier
reads the actual saved Markdown and an exported assistant review; it does not
accept a CLI success or a claimed template revision as proof of layout adoption.
Without complete native invocation evidence its result is **unverified**, even
when every artifact check passes. No native run is recorded by adding this suite.

## Prepare the isolated candidate

Freeze the candidate after assembly and deterministic checks. Run:

```powershell
node evals/template-updates.mjs seed
```

The returned `fixture.json` lives below repository `.temp/template-update-host/`.
Use only its synthetic vault, explicit `stateRoot`, and generated paths. Do not
point the host at personal preferences or a real vault. Do not edit the fixture
manifest. Reseed if the candidate changes. Preserve raw exports locally under
the fixture's `evidenceRoot`; do not commit private host or account information.

The fixture includes an exact known 0.2.0 bundled daily-plan checklist, a separately
customized compact chat-review template, canonical records, an existing plan for
the host's local day, and an earlier plan. Today's plan has an in-progress carried
task, completed and cancelled tasks, an unresolved reference, delegated work,
original identity/creation time, notes and explicit carry provenance. A separate
unselected task is available for a new future plan.

Run a fresh authenticated native host session with explicit registration of this
candidate plugin. Capture the host invocation/session identity, plugin registration
and discovered **installed** skill paths. Record the exact installed hashes for
`skills/daily-tasks/SKILL.md` and `skills/daily-tasks-plan/SKILL.md`; they must match
the candidate. Repository AGENTS.md loading, direct CLI execution, fixture seeding,
or a chat which merely has the plugin's skill text pasted into it does not establish
native discovery. Record host version and model; unavailable evidence stays unverified.

## Native interaction and captures

Use the fixture's actual date and paths when replacing the words in angle brackets.
The four quoted decision sentences below are receipt anchors: send them as actual
user messages. Export the original messages with roles intact; never rewrite an
assistant decision as a user message. A human should inspect both the comparison
and the saved output, including Markdown rendering, for mistakes outside the
fixture's structural checks.

1. Ask: “Use only the synthetic Daily Tasks vault at `<vaultRoot>` and its existing
   profile at `<stateRoot>`. Review the available daily-plan template update before
   authoring anything. Show the old and new layout comparison. Preserve the existing
   plan and selections while I choose.” Confirm the old checklist is recognized
   and the new table revision is offered. Send **“Keep the current daily-plan layout
   for this revision.”** Copy the actual unchanged `paths.today` to
   `paths.declinedPlan`. Run another ordinary planning review without asking to
   revisit template choices; the same declined revision must not
   be offered repeatedly. Inspect persisted choices and transcript, not only prose.
2. Ask to revisit that daily-plan template decision. Send **“Use the new daily-plan
   layout for new documents only.”** Then ask: “Create the plan for `<future>` with
   only New task (`<ids.newTask>`). Leave today's existing plan unchanged.” Copy the
   actual future plan to `paths.acceptedPlan`, and the still-unchanged existing plan
   to `paths.existingAfterAcceptance`. The new plan must contain the current grouped
   table layout, required columns, counts and legend; the existing plan must still
   use the checklist. The accepted new-document task must be the sole selected row.
3. Send **“Also reformat today’s existing plan using the new daily-plan layout.”**
   Explicitly ask to reconcile first, preserve the selected task order, states,
   links, carry reference, unresolved reference and notes, and keep original plan
   identity/creation time. Copy the actual updated `paths.today` to
   `paths.reformattedPlan`. Verify completed and cancelled rows remain visible,
   delegated work stays delegated, no historical/canonical record was rewritten,
   and the old local template file remains intact.
4. Send **“Keep my compact chat-review template unchanged.”** Ask to display today's
   review using that configured template, with no saved-document changes. Export
   the **actual assistant message**, byte for byte, into `paths.chatReview`. The
   compact “My compact review”, “Chosen work”, and “Other available work” checklist
   structure must remain independent from the new saved daily-plan tables. Capture
   a standalone review message so the exported text is exactly one original
   assistant message; do not manually reconstruct a plausible review.

Copy snapshots immediately at each boundary, before the next action. Captures are
copies of actual host output, not substitute documents authored by the evaluator.
Observe and retain the host's preparation, template revision decisions, checkpoints,
file-tool writes and verification. Do not use a direct CLI or a test-only writer to
perform the host's Markdown changes. The scripted verifier checks the artifact
invariants; the human transcript review must also confirm the comparison, decline
suppression, explicit revisit, and reconciliation happened in the requested order.

## Receipt and verification

Create a JSON receipt under `evidenceRoot` from the native exports. SHA-256 values
for invocation, discovery, transcript and output files are hashes of exact file
bytes; installed skill hashes normalize CRLF to LF, like candidate inventory.
All evidence and installed-skill paths are absolute. The `candidateHash` comes
from `fixture.candidate.hash`.

```json
{
  "schemaVersion": 1,
  "execution": "native-host",
  "isolated": true,
  "host": {"name": "ACTUAL_HOST", "version": "ACTUAL_VERSION", "model": "ACTUAL_MODEL", "sessionId": "ACTUAL_SESSION"},
  "candidateHash": "FIXTURE_CANDIDATE_HASH",
  "invocation": {"path": "ABSOLUTE_INVOCATION_EXPORT", "sha256": "EXACT_HASH"},
  "discovery": {"path": "ABSOLUTE_DISCOVERY_EXPORT", "sha256": "EXACT_HASH"},
  "transcript": {"path": "ABSOLUTE_TRANSCRIPT_JSON", "sha256": "EXACT_HASH"},
  "loadedSkills": [
    {"source": "skills/daily-tasks/SKILL.md", "path": "ABSOLUTE_INSTALLED_SKILL", "sha256": "NORMALIZED_HASH"},
    {"source": "skills/daily-tasks-plan/SKILL.md", "path": "ABSOLUTE_INSTALLED_PLAN_SKILL", "sha256": "NORMALIZED_HASH"}
  ],
  "outputs": {
    "declinedPlan": {"path": "FIXTURE_PATHS_DECLINED_PLAN", "sha256": "EXACT_HASH"},
    "existingAfterAcceptance": {"path": "FIXTURE_PATHS_EXISTING_AFTER_ACCEPTANCE", "sha256": "EXACT_HASH"},
    "acceptedPlan": {"path": "FIXTURE_PATHS_ACCEPTED_PLAN", "sha256": "EXACT_HASH"},
    "reformattedPlan": {"path": "FIXTURE_PATHS_REFORMATTED_PLAN", "sha256": "EXACT_HASH"},
    "chatReview": {"path": "FIXTURE_PATHS_CHAT_REVIEW", "sha256": "EXACT_HASH"}
  }
}
```

The transcript JSON has `{"messages":[{"role":"user","content":"..."}, ...]}`.
Retain tool messages too. Invocation evidence must contain the actual host name
and session ID, and discovery evidence must contain the installed skill paths.
Do not manufacture these files when the host does not expose the evidence.
An evaluator still needs to confirm export provenance: hashes establish unchanged
bytes, not an authenticated host or proof of human authorization.

```powershell
node evals/template-updates.mjs verify ABSOLUTE_FIXTURE_JSON ABSOLUTE_NATIVE_RECEIPT_JSON
```

Omit the receipt to inspect artifacts while retaining `unverified`. Exit code 0
requires both passing artifact checks and complete matching native evidence;
`unverified` and `fail` return exit code 1. The final live today/future documents
must equal their final captured copies. Candidate changes, missing exports,
missing choices, changed evidence or undiscovered skills cannot pass.

`node --test test/template-evaluation.test.mjs` calibrates the oracle with synthetic
correct/incorrect outputs. It rejects checklist-as-table labels, wrong columns,
changed IDs/creation times/statuses/order/links, removed carry or unresolved
references, lost notes and accidental review-layout adoption. Those tests are
deterministic verifier evidence only; they never establish native activation.

The broader policy matrix (all template kinds, latest/keep/ask, first-use, revision
decisions, scope inheritance, cache removal, interrupted persistence and retries)
belongs to feature integration tests. This host scenario addresses the distinct
risk that an agent chooses a revision correctly but authors the wrong layout.
