# User formatting templates

> [!IMPORTANT]
> **Scope Directive**: This document defines the registration, resolution, portable path conventions, and authoring adaptation rules for user-supplied or visible Markdown formatting templates (`projectIndex`, `dailyPlan`, `milestone`, `task`, `planDayReview`). It is strictly a template specification and adaptation contract. Low-level CLI commands and signatures belong in [`cli.md`](cli.md), template lifecycle policies and upgrade offers in [`template-updates.md`](template-updates.md), transactional write-ahead checkpointing in [`operations.md`](operations.md), and record schemas, frontmatter, and DoD invariants in [`records.md`](records.md).

Templates provide visible layout, headings, spacing, and styling preferences. A template is formatting guidance only; it never conveys task acceptance, execution authority, or executable commands.

## Template registration and configuration

### 1. Visible workspace templates
- During workspace setup or first relevant use, `template-prepare` proposes file placement for needed template kinds.
- Follow the placement proposal to place templates where users can open and edit them (e.g. `./templates/` or `./3-resources/templates/`).
- If creating a visible template, save the initial baseline via `template-state` action `baseline` in `baselineScope` before creating the Markdown file.
- Register the portable workspace-relative path under `templates.<kind>` in the project profile (or home profile for user-scoped templates).
- Validated profiles use `validate-profile`. Project-level profile changes are logged via the decision log.

### 2. Profile configuration schema
Save portable paths in the profile's optional `templates` map:

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

- **Portable paths**: Use `./` for workspace-relative paths, `~/` for user home paths, or explicit absolute paths.
- **Inheritance & resets (Schema v2)**:
  - Omitting a key inherits the template setting from the parent/user layer.
  - Setting a key to `null` resets to the bundled default formatting, masking inherited user templates.
- **Missing files**: If a configured file is missing, the system falls back to its retained baseline snapshot if available; otherwise, report the missing path and prompt for replacement or reset.

### 3. Template kinds
- `projectIndex`: Controls formatting for `project-index.md` files.
- `dailyPlan`: Controls the saved daily plan document (`YYYY.MM.DD-daily-plan.md`).
- `milestone`: Controls milestone overview documents.
- `task`: Controls individual task documents.
- `planDayReview`: Controls interactive planning review screens displayed to the user (distinct from the saved daily plan).

## Authoring and adapting content

When generating documents using active templates:

### Replace examples with actual data
- Replace sample task names, dates, identities, owners, and relationships with actual accepted record data.
- Never copy provisional sample notices or template-level `document-maturity` tags into live records.
- Completed example files serve as structural guides; explicit placeholders are optional.

### Enforce technical and domain invariants
A custom template layout cannot override canonical record contracts:
- **Metadata & Frontmatter**: Retain required YAML scalar frontmatter (`id: UUIDv7`, `type`, `title`, `owner`, dates, state).
- **Definition of Done**: Tasks and milestones must retain the recognized `## Definition of Done` heading with criteria checkboxes and UUIDv7 comments. Standalone DoD files are prohibited.
- **View Projections**: Links in indexes and daily plans must use `[[relative-path|Task title]] <!-- ref: UUIDv7 -->` with standard status symbols.
- **Section Mapping**: Map custom headings to required functional roles (e.g. separating personal work from delegated work in daily plans) rather than discarding role separation.
- **Formatting Conflicts**: If a user template cannot represent required technical facts (e.g. lacks frontmatter or status representations), explain the conflict clearly; never discard canonical facts to mimic layout.

### Existing documents vs new output
- Configured templates govern **newly created** documents.
- Ordinary edits to existing files preserve their established structure and user prose.
- Reformatting existing documents requires an explicit user request and follows the write-ahead checkpoint and baseline protocol ([`operations.md`](operations.md)).
