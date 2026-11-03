---
id: F-00.01
group: "00"
status: implemented
---

# F-00.01 Workspace, Identity & Template Setup

## Summary

Configure personal identity, local timezone, daily priorities, workspace storage locations, and customizable document templates with controlled template update preferences.

## User Need

Users need a one-time setup and explicit update workflow that establishes who they are, their local timezone, where their project and daily plan files live, and how their documents should be formatted, without forcing a rigid folder layout or overwriting customized templates unexpectedly.

## Conceptual Context

- [C-01: Canonical Work Records & Embedded Definition of Done](../../concepts/c-01-canonical-work-records.md) — establishes workspace roots and customizable document templates for each record type.
- [C-02: Local-Day Plan, Rollover & Carried Selections](../../concepts/c-02-local-day-plan-and-rollover.md) — configures the user's local timezone and daily plan template.

## Use Cases

- [UC-00.01.01: Set Up Workspace, Identity & Templates](uc-00.01.01-setup-workspace-and-templates.md)

## Scope

- Capture and persist personal preferences (user name, email address, local timezone, and personal priorities) separately from workspace folder bindings.
- Reuse existing personal and workspace settings automatically on subsequent requests without re-prompting.
- Support both existing structured knowledge vaults and ordinary folders for storing projects and daily plans without creating unwanted folder hierarchies.
- Allow users to register custom templates or completed document examples for projects, milestones, tasks, daily plans, and planning screens.
- Compare updated bundled templates against active user templates, offer previews, and honor per-template update policies (**Ask about updates**, **Always use latest**, or **Keep current**).

## Out of Scope

- Creating or updating individual projects, milestones, tasks, or blockers (owned by [F-01.02](../f-01.02/feature.md)).
- Authorizing external email or chat accounts (owned by [F-00.03](../f-00.03/feature.md)).
- Automatically reformatting existing project or daily plan documents without an explicit user request.

## Inputs

- User name, email address, local timezone, and optional personal priorities.
- Chosen workspace path, projects folder location, and daily plans folder location.
- Optional custom template files, example documents, and template update policy choices.

## Outputs

- Saved personal and workspace preference profiles that persist across sessions.
- Active document templates placed or linked in the workspace when requested.
- Clear preview and confirmation prompts whenever bundled templates change.

## Acceptance

- Personal preferences can be saved and reused across workspaces without requiring a workspace folder until work records are managed.
- Workspace folder bindings resolve consistently regardless of the current working folder.
- Supplying a custom template or example applies that layout to newly created documents of that kind while leaving existing documents untouched unless reformatting is requested.
- When a bundled template changes, the user is shown a preview and can adopt the update, keep their current template, or postpone without losing manual template edits.

## Dependencies

None.
