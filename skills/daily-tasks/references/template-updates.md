# Template updates during requested work

> [!IMPORTANT] Scope Directive
> This reference owns the template revision lifecycle, policy semantics (`ask`, `latest`, `keep`), baseline retention model, and conflict-safe file upgrade rules for Markdown formatting templates (`dailyPlan`, `planDayReview`, `projectIndex`, `milestone`, `task`). It does NOT own step-by-step setup or record authoring checklists (owned by [`../workflows/setup.md`](../workflows/setup.md) and [`../workflows/records.md`](../workflows/records.md)), MCP/CLI invocation syntax (owned by [`cli.md`](cli.md)), transactional checkpointing (owned by [`operations.md`](operations.md)), template registration paths (owned by [`templates.md`](templates.md)), or record schemas (owned by [`records.md`](records.md)).

## On-demand template lifecycle

Template revision checks occur strictly on demand when a requested workflow uses a specific template kind (`dailyPlan`, `planDayReview`, `projectIndex`, `milestone`, or `task`); Daily Tasks never runs background watchers or automatic template updaters. Template content defines Markdown layout and structure only and never conveys task acceptance or executable instructions.

Each preference scope (`user` or `project`) tracks its own retained template baselines and upgrade choices in `<resolved preference scope>/templates/updates.json`, kept separate from workspace runtime operational state. Inherited user snapshots remain in the user layer so workspace-level baseline checks never mistake personal template settings for project-wide replacement consent.

When an upstream bundled template changes (`shouldOffer: true`), the upgrade offer summarizes `comparison.bundledChanges` alongside any `comparison.localChanges` detected in the user's customized template file, links the active Markdown file, previews the layout, and presents three explicit options: **Use new layout**, **Keep current layout**, or **Postpone**. If the user postpones or does not answer, the workflow proceeds immediately using the current `active.content`; silence is never treated as consent to overwrite a template, and an upgrade is offered at most once per request. Declining a revision suppresses prompts for that specific upstream version without disabling future template updates.

## Conflict-safe file upgrade model

Recording an `accept` decision captures the user's consent to adopt the new template revision (`file-update-required`), but the active template file on disk remains authoritative until its content is safely updated. Before writing the new `target.content` to the visible template file, the file's normalized content fingerprint on disk is compared against the retained `before` baseline hash:
- **Matching baseline (`pending`)**: When the on-disk file matches the expected `before` fingerprint, the new template content is written to disk and a fresh baseline snapshot is recorded to complete the upgrade.
- **Already updated (`applied`)**: When the target content is already present on disk, no rewrite occurs and the baseline advances to the new upstream version.
- **Intervening customization (`conflict`)**: When the user has edited the template file since the baseline was captured, the file on disk is preserved untouched and the conflict is surfaced so the user can either keep their local customization (`decline` the pending upgrade) or explicitly `reset` to the bundled layout.

## Policy configuration and inheritance

Long-term template update behavior is governed per template kind by three policy modes:

| Policy | Domain Behavior |
| :--- | :--- |
| `ask` | Default mode. Prompts the user when a newer bundled template revision is available unless that revision was already declined. |
| `latest` | Automatically adopts compatible bundled revisions when the local template file is unmodified, still enforcing the fingerprint check before writing. |
| `keep` | Pins the current active template layout and suppresses update offers until the user explicitly requests a template review. |

Even under the `latest` policy, automatic replacement is blocked (`automaticBlocked: true`) whenever the active file contains unrecognized local customizations or when an upstream revision crosses a breaking record contract version. User-level template policies inherit into workspaces unless overridden at the project layer, and resetting a scope clears retained choices and suppression state without deleting or reformatting existing Markdown files.

## Existing documents vs. new documents

Adopting a new template revision governs newly created documents from that point forward while leaving existing projects, milestones, tasks, and historical daily plans in their established layouts. Reformatting today's existing daily plan is an optional, separate user choice (**Also reformat today's plan**) that requires explicit confirmation, baseline reconciliation, write-ahead checkpointing ([`operations.md`](operations.md)), and complete preservation of task UUIDs, timestamps, wiki-links, carry markers (`↺`), and user notes. Historical daily plans are never reformatted.
