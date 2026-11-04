# User formatting templates

> [!IMPORTANT] Scope Directive
> This reference owns the template registration schema, portable path conventions, inheritance/reset semantics, and domain invariant preservation rules for visible Markdown formatting templates (`projectIndex`, `dailyPlan`, `milestone`, `task`, `planDayReview`). It does NOT own step-by-step setup or authoring workflows (owned by [`../workflows/setup.md`](../workflows/setup.md) and [`../workflows/records.md`](../workflows/records.md)), MCP/CLI invocation syntax (owned by [`cli.md`](cli.md)), template upgrade policies (owned by [`template-updates.md`](template-updates.md)), transactional checkpointing (owned by [`operations.md`](operations.md)), or canonical record schemas (owned by [`records.md`](records.md)).

## Template registration and configuration

Formatting templates control the visible headings, section ordering, spacing, and table styling of Daily Tasks documents. A template is strictly a presentation contract and never grants task acceptance, alters ownership, or embeds executable commands.

During workspace setup or first use of a template kind, active templates are placed in a visible workspace directory (such as `./templates/` or `./3-resources/templates/`) where the user can inspect and edit them directly, with initial baselines recorded in `<resolved preference scope>/templates/updates.json` and portable paths registered under the `templates` map in `profile.json`:

```json
{
  "templates": {
    "projectIndex": "./templates/project-index.md",
    "dailyPlan": "~/templates/daily-plan.md",
    "milestone": "./templates/milestone.md",
    "task": "./templates/task.md",
    "planDayReview": "./templates/plan-day-review.md"
  }
}
```

Template paths use `./` for workspace-relative locations, `~/` for user-home locations, or explicit absolute paths. Under Schema Version 2 profile inheritance, omitting a template key in the workspace profile inherits the corresponding template from the user profile, whereas setting a key to `null` explicitly resets that kind to the bundled default and masks any user-level template. If a registered template file is missing on disk, resolution falls back to its retained baseline snapshot when available or reports the missing path so the user can replace or reset it.

The five supported template kinds cover the complete document surface:
- **`projectIndex`**: Layout for `project-index.md` overview files.
- **`dailyPlan`**: Layout for persisted daily plan files (`YYYY.MM.DD-daily-plan.md`).
- **`milestone`**: Layout for milestone definition files (`m{N}-{name}.md`).
- **`task`**: Layout for individual task records (`t{N}-{name}.md`).
- **`planDayReview`**: Layout for interactive planning review screens rendered in chat (independent of the saved `dailyPlan` layout).

## Domain invariant preservation during adaptation

When rendering a new document from an active template, sample placeholders, example task titles, sample dates, and template-level maturity notices (`document-maturity`) are replaced with the accepted record's actual metadata and content.

Customizing a template's visual layout never overrides canonical domain invariants ([`records.md`](records.md)):
- **Scalar YAML frontmatter**: Every record retains required scalar YAML frontmatter (`id` as UUIDv7, `type`, `title`, `owner`, UTC timestamps, and lifecycle state).
- **Embedded Definition of Done**: Tasks and milestones retain a single embedded `## Definition of Done` section with checkbox items and `<!-- id: UUIDv7 -->` comments; standalone DoD files are never created.
- **View reference links**: Index and daily-plan projections retain readable wiki-links paired with hidden UUID comments (`[[relative-path|Task title]] <!-- ref: UUIDv7 -->`, escaping pipes as `\|` in tables) and canonical status markers (`[ ]`, `[>]`, `[x]`, `[-]`).
- **Role separation**: Custom daily-plan headings map cleanly onto the three ownership/assignment roles (`My work`, `Delegated work`, and `Follow-up work`) rather than collapsing personal and delegated tasks together.

If a user-supplied template omits required technical structures (such as frontmatter or status representations), the conflict is explained to the user rather than discarding canonical metadata to match the broken layout. Configured templates govern newly created documents only; routine updates to existing records preserve their established layout and user prose via surgical CST edits unless the user explicitly requests a document reformat under the write-ahead checkpoint model ([`operations.md`](operations.md)).
