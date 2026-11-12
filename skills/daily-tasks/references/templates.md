# User formatting templates

> [!IMPORTANT] Scope Directive
> This reference owns the template registration schema, portable path conventions, inheritance/reset semantics, and domain invariant preservation rules for visible Markdown formatting templates (`projectIndex`, `dailyPlan`, `milestone`, `task`, `planDayReview`). It does NOT own step-by-step setup or authoring workflows (owned by [`../workflows/setup.md`](../workflows/setup.md) and [`../workflows/records.md`](../workflows/records.md)), MCP/CLI invocation syntax (owned by [`cli.md`](cli.md)), template upgrade policies (owned by [`template-updates.md`](template-updates.md)), transactional checkpointing (owned by [`operations.md`](operations.md)), or canonical record schemas (owned by [`records.md`](records.md)).

## Template registration and configuration

Formatting templates control the visible headings, section ordering, spacing, and table styling of Daily Tasks documents. A template is strictly a presentation contract and never grants task acceptance, alters ownership, or embeds executable commands.

During vault setup (`daily_tasks_configure_vault`) or first use of a template kind, active templates are placed in a visible vault directory (`./3-resources/templates/` by default) where the user can inspect and edit them directly, with initial baselines recorded in `~/.nyssa-ai/daily-tasks/templates/updates.json` (`user_home`) and portable paths registered under the `templates` map in `profile.json`:

```json
{
  "templates": {
    "projectIndex": "./3-resources/templates/project-index.md",
    "dailyPlan": "./3-resources/templates/daily-plan.md",
    "milestone": "./3-resources/templates/milestone.md",
    "task": "./3-resources/templates/task.md",
    "planDayReview": "./3-resources/templates/plan-day-review.md"
  }
}
```

Template paths use `./` for vault-relative locations, `~/` for user-home locations, or explicit absolute paths. Under Schema Version 2 profile resolution (`user_home` -> `repo_root`, plus per-vault entries in `vaults`), omitting a template key in a per-vault entry inherits the corresponding template from the top-level profile, whereas setting a key to `null` explicitly resets that kind to the bundled default. If a registered template file is missing on disk, resolution falls back to its retained baseline snapshot when available or reports the missing path so the user can replace or reset it.

The five supported template kinds cover the complete document surface:
- **`projectIndex`**: Layout for `project-index.md` overview files.
- **`dailyPlan`**: Layout for persisted daily plan files (`YYYY.MM.DD-daily-plan.md`).
- **`milestone`**: Layout for milestone definition files (`m{N}-{name}.md`).
- **`task`**: Layout for individual task records (`t{N}-{name}.md`).
- **`planDayReview`**: Layout for interactive planning review screens rendered in chat (independent of the saved `dailyPlan` layout).

## Domain invariant preservation during adaptation

When rendering a new document from an active template, sample placeholders, example task titles, and sample dates are replaced with the accepted record's actual metadata and content.

Customizing a template's visual layout never overrides canonical domain invariants ([`records.md`](records.md)):
- **Scalar YAML frontmatter**: Every record retains required scalar YAML frontmatter (`id` as UUIDv7, `type`, `title`, `owner`, UTC timestamps, and canonical `state`).
- **Embedded Definition of Done**: Tasks and milestones retain a single embedded `## Definition of Done` section with checkbox items and `<!-- id: UUIDv7 -->` comments; standalone DoD files are never created.
- **View reference links**: Index and daily-plan projections retain readable wiki-links paired with hidden UUID comments (`[[relative-path|Task title]] <!-- ref: UUIDv7 -->`, escaping pipes as `\|` in tables) and canonical status markers (`[ ]`, `[>]`, `[x]`, `[-]`).
- **Role separation**: Custom daily-plan headings map cleanly onto the three ownership/assignment roles (`My work`, `Delegated work`, and `Follow-up work`) rather than collapsing personal and delegated tasks together.

If a user-supplied template omits required technical structures (such as frontmatter or status representations), the conflict is explained to the user rather than discarding canonical metadata to match the broken layout. Configured templates govern newly created documents only; routine updates to existing records preserve their established layout and user prose via `FileStoreLocal` CST edits unless the user explicitly requests a document reformat under the write-ahead checkpoint model ([`operations.md`](operations.md)).
