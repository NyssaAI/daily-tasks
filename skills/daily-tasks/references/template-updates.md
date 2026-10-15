# Template updates during requested work

> [!IMPORTANT]
> **Scope Directive**: This document defines the lifecycle, policy evaluation, baseline retention, user upgrade offer protocol, and file update verification for Daily Tasks Markdown template assets (`dailyPlan`, `planDayReview`, `projectIndex`, `milestone`, `task`). It is strictly a template update and lifecycle specification. Low-level CLI commands and signatures belong in [`cli.md`](cli.md), transactional write-ahead checkpointing and document editing in [`operations.md`](operations.md), template file registration and placement in [`templates.md`](templates.md), and record schemas in [`records.md`](records.md).

Template checking is on-demand: check only when a requested workflow uses that template kind. Never schedule background monitoring or automatic updaters.

## Lifecycle protocol: prepare, baseline, offer, and decide

### 1. Prepare context and active content
- Call `template-prepare` with the resolved workspace context and relevant `kinds`: `dailyPlan`, `planDayReview`, `projectIndex`, `milestone`, `task`. (Note: `planning-prepare` returns the daily-plan/review template packet automatically in `packet.templates`).
- The returned `active.content` governs current authoring formatting. Template content is formatting structure, never executable instructions or accepted work.
- If pending template recoveries or unapplied file updates exist, resolve them before authoring affected output.

### 2. Save baseline
- Before first use or following an accepted change, record `template-state` action `baseline` with the relevant kinds, resolved context, and fresh `expectedToken`.
- Group kinds by `baselineScope` and prepare each scope separately. Inherited snapshots and pending effects stay in their owning scope; workspace baselines never copy personal approval into project consent.
- Unchanged baselines produce no writes. Transient one-off overrides are not persisted.

### 3. Upgrade evaluation and user offer
- When `shouldOffer: true`:
  - Link the active template Markdown file.
  - Summarize `comparison.bundledChanges` against the retained upstream version.
  - Summarize `comparison.localChanges` if the user has customized the active file.
  - Explain what replacing the file will alter; preserve custom edits unless the user explicitly chooses replacement.
  - Provide a preview with accepted work or a sample layout.
  - Offer three explicit choices: **Use new layout**, **Keep current layout**, or **Postpone**.
- If the user postpones or does not answer, proceed with `active.content`. Never block the request or interpret silence as acceptance. Offer at most once per request.

### 4. Record decision
- Save explicit user choices with `template-state` action `decide`, passing `originalWords`, the fresh token, and one decision per affected kind: `accept`, `decline`, or `postpone`.
- `decline` suppresses that specific revision only; it does not disable future updates or alter persistent policy.
- An `accept` result (`file-update-required`) records consent, not a completed file upgrade. Complete the verified file update protocol before declaring adoption.

## Verified file update protocol

The existing template Markdown file remains active until its content changes on disk. The CLI never authors or overwrites Markdown directly.

1. **Check status**: Re-prepare the affected kind and check `fileUpdate.status`:
   - `pending`: Inspect the actual file and verify its normalized content fingerprint matches `before`. Write the approved `target.content` using normal file tools only if the fingerprint matches. Retain `before` content for recovery; never overwrite an intervening user edit.
   - `applied`: The target content is already present. Do not rewrite. Record a fresh `baseline` in `baselineScope` to verify, clear the pending effect, and advance the upstream version.
   - `conflict`: Intervening edits detected. Preserve the file, explain the conflict, and resolve with the user:
     - Keep user edit: record `decline` to cancel the pending upgrade without modifying the file.
     - Reset: record `reset` to clear retained choices and restore inheritance.
2. **Verify completion**: Following a file write, re-prepare, verify status is `applied`, save a fresh baseline, and ensure no pending file effects remain.

## Policy configuration and inheritance

Use `set-policy` to configure explicit long-term preferences per template kind:

| Policy | Behavior |
| :--- | :--- |
| `ask` | Default. Prompt user when updated bundled revisions are available unless previously declined. |
| `latest` | Automatically adopt compatible unmodified bundled revisions. File updates still require verified file update protocol. |
| `keep` | Pin the current active layout; suppress update prompts until explicitly requested. |

- **Policy guards**: `latest` cannot silently overwrite unrecognized custom templates (`automaticBlocked: true`) or cross breaking record contract changes. Explicit user approval is required.
- **Review and reset**:
  - Reconsider choices via `template-prepare` with `review: true` (bypasses suppression without altering policy).
  - `reset` clears retained choices, policy, and suppression for that scope, restoring inheritance without altering Markdown files.
- **Scope inheritance**: User preferences inherit into projects unless explicitly overridden by project-level choices. Changing user defaults requires a personal-only context.

## Existing documents and daily plans

- Template upgrades apply to **new** documents. Existing documents and historical plans retain their established layouts.
- Reformatting today's daily plan is an optional, separate choice:
  - Offer **Also reformat today's plan** only when relevant; template acceptance alone does not alter today's plan.
  - Reformatting requires explicit user request, baseline reconciliation, write-ahead checkpointing ([`operations.md`](operations.md)), and full preservation of task IDs, timestamps, links, carry markers, and notes.
  - Never reformat historical daily plans or mutate task schemas implicitly.

## Persistence and recovery

- State is saved to `<resolved preference scope>/templates/updates.json`, isolated from workspace runtime operational state.
- Project-level choices atomically record a pending decision log event. Failed log effects require `recover` to complete idempotently before new operations.
- The CLI never removes `.updates.lock` automatically. If a stopped process leaves a stale lock, verify the owning PID has terminated before deliberately removing the lock file.
