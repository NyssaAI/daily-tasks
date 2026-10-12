# Template update contract

The plugin ships five independently fingerprinted layouts: `dailyPlan`,
`planDayReview`, `projectIndex`, `milestone`, and `task`. Revisions are SHA-256 of
Markdown with CRLF normalized to LF, independent of package version. The catalog
validates historical fingerprints against retained source content and records Git
provenance. Only exact known content is recognized as a bundled copy. Edited or
unknown content is custom; its source is never overwritten.

## Preparation and adoption

`template-prepare` accepts normal resolved-context selectors plus nonempty distinct
`kinds`, optional `scope`, and optional `review: true`. It returns active and available
content/revisions, source, policy, per-revision decisions, visible comparison,
compatibility, offer decision, storage hashes and an optimistic token. Preparation is
read-only. `planning-prepare` includes the same packet for dailyPlan and planDayReview.

`template-state` takes the same context and kinds, `expectedToken`, and action:

| Action | Purpose |
| --- | --- |
| `baseline` | Retain observed content or apply an already opted-in compatible update. Observation is not acceptance. |
| `decide` | Save explicit `decisions`, one per kind, and the user's `originalWords`. |
| `recover` | Finish a pending event after any abandoned lock has been deliberately cleared. |

Each decision is `{kind, action}`. Actions are `accept`, `decline`, `postpone`,
`review` (remove this scope's suppression), `reset` (remove this scope's choice),
or `set-policy` with `policy: "ask"|"latest"|"keep"`. `review: true` also permits
an explicit comparison while a policy or inherited decline suppresses routine offers.
`dryRun: true` writes nothing. Reprepare after every write; changed sources or choices
reject stale tokens. Exact mutation retries do not duplicate effects.

`ask` offers new revisions; a declined revision is suppressed until revisited or a
different revision arrives. `latest` adopts only an established compatible record
contract. Custom or changed contracts require review. `keep` retains the active
snapshot until explicitly changed. Policies are per kind and opt-in; declining one
offer leaves policy unchanged. Skills offer previews using actual work and use
`active.content` for authoring. Silence and postponement continue the current layout.

## Configuration and retention

JSON snapshots live at `<context.writableScopes[scope]>/templates/updates.json`.
These are configuration assets, not vault operating state. No new profile fields or
automatic migrations are introduced. Version 1 exclusive profiles and version 2
user/project layering reuse the existing resolver, accepted roots, and legacy paths.
An explicit scope wins; otherwise use the resolved project scope (legacy when
exclusive), or user scope for personal-only configuration. Relative template paths
still resolve against the bound vault or home, never later process cwd.

Entries bind to the winning profile source and configured path/content. A changed
path, profile null mask, or edited custom source invalidates an older binding.
Scoped reset removes only that scope's template entry and exposes a matching lower
layer. A recorded project observation does not shadow a deliberate personal choice;
an explicit project choice does. Policies inherit when omitted and override when
explicit. Current-task overrides are transient and cannot be persisted.

An active snapshot survives a removed source or older plugin cache. Without a
retained snapshot, missing configured content requires a replacement/reset.
Unreadable, corrupt or unsafe paths fail visibly. If no metadata exists, observe the
configured file or current bundled content; never claim knowledge of earlier adoption.

## Writes, logging and documents

The module writes JSON only, using a scoped lock, checked hashes and atomic replace.
Consequential project choices checkpoint an exact `templates.changed` event before
appending through the existing log API. A failed append remains pending and recovery
retries that exact event once. Baselines and personal-only settings do not create
vault log events. Complete owner metadata is written and synced before exclusive
same-directory hard-link acquisition. Existing locks are never automatically broken,
even when their owner is stopped: that check/unlink sequence can race another
recoverer. As with the log, deliberate removal requires verifying the stopped owner
and excluding concurrent writers/recovery; live or unknown ownership blocks it.
The preference filesystem must support same-directory hard links; unsupported
storage fails visibly rather than using unsafe lock creation.

Skills own interactions and Markdown. Adoption changes future authoring only;
reformatting today's plan requires a separate explicit decision, reconciliation and
the established operation checkpoint protocol. Preserve IDs, original creation time,
selections, order, statuses, links, carry provenance, notes and unresolved references.
Historical records and original custom templates remain untouched. Output must match
the chosen visible layout while satisfying current mandatory record contracts.

## Verification boundary

Behavior tests cover fingerprints, decisions, policies, scopes, retention, stale
tokens and recovery using synthetic roots. The [host evaluation](../evals/template-updates.md)
checks saved documents and captured chat layout plus explicit choice evidence. Its
calibration tests and direct CLI execution are not native-host activation evidence.
No background monitor, scheduler or separate plugin updater is included.
