---
id: F-00.01
group: "00"
status: implemented
---

# F-00.01 Vault, Identity & Template Setup

## Summary

Configure personal identity, local timezone, daily priorities, vault folder locations, and customizable document templates with controlled template update preferences.

## User Need

Users need a one-time setup and explicit update workflow that establishes who they are, their local timezone, where their project and daily plan files live inside their vault, and how their documents should be formatted, without forcing a rigid folder layout or overwriting customized templates unexpectedly.

## Conceptual Context

- [C-01: Canonical Work Records & Embedded Definition of Done](../../concepts/c-01-canonical-work-records.md) — establishes vault roots and customizable document templates for each record kind.
- [C-02: Local-Day Plan, Rollover & Carried Selections](../../concepts/c-02-local-day-plan-and-rollover.md) — configures the user's local timezone and daily plan template.

## Use Cases

- [UC-00.01.01: Set Up Vault, Identity & Templates](uc-00.01.01-setup-vault-and-templates.md)

## Scope

- Capture and persist personal preferences (user name, email address, local timezone, and personal priorities) alongside per-vault folder bindings under user configuration (`~/.nyssa-ai/daily-tasks/`), keeping zero `.nyssa-ai/` files inside the vault.
- Reuse existing personal and vault settings automatically on subsequent requests without re-prompting.
- Support both structured PARA knowledge vaults and ordinary non-PARA folders (defaulting to `1-projects` and `2-areas/daily-plans` unless customized), while rejecting agent persona runtime directories as vaults.
- Allow users to register custom templates or completed document examples for projects, milestones, tasks, blockers, and daily plans.
- Compare updated bundled templates against active user templates, offer previews, and honor per-template update policies (**Ask about updates**, **Always use latest**, or **Keep current**).

## Out of Scope

- Creating or updating individual projects, milestones, tasks, or blockers (owned by [F-01.02](../f-01.02/feature.md)).
- Authorizing external email or chat accounts (owned by [F-00.03](../f-00.03/feature.md)).
- Automatically reformatting existing project or daily plan documents without an explicit user request.

## Inputs

- User name, email address, local timezone, and optional personal priorities.
- Chosen vault path (`vault_root`), projects folder location, and daily plans folder location.
- Optional custom template files, example documents, and template update policy choices.

## Outputs

- Saved personal and per-vault preference profiles in `~/.nyssa-ai/daily-tasks/` that persist across sessions without writing `.nyssa-ai/` into the vault.
- Active document templates placed or linked in the vault when requested.
- Clear preview and confirmation prompts whenever bundled templates change.

## Acceptance

- Personal preferences can be saved and reused across vaults without requiring a vault folder until work records are managed.
- Vault folder bindings resolve consistently regardless of the current working folder, and agent persona runtime folders are rejected as vault paths.
- Supplying a custom template or example applies that layout to newly created documents of that kind while leaving existing documents untouched unless reformatting is requested.
- When a bundled template changes, the user is shown a preview and can adopt the update, keep their current template, or postpone without losing manual template edits.

## Dependencies

None.
