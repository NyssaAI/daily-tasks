---
name: daily-tasks-capture
description: Capture possible tasks, projects and milestones as candidates, deduplicate against existing work and obtain explicit individual or batch acceptance before creation. Use when extracting action items from notes or messages, collecting possible commitments, or reviewing candidates for acceptance; hand accepted work to Records for creation.
---

# Capture and accept

Resolve configured scope through [setup](../daily-tasks-setup/SKILL.md). Read only the
user-supplied/authorized sources and [record conventions](../daily-tasks/references/records.md).
Distinguish requests, promises, ideas and updates. Match existing UUID/source references
before proposing a new item. A repeated mention adds context, not another task.

Present a compact candidate list with proposed title, parent milestone/project, owner,
assignee if specified, target_date only if explicit, source reference and unresolved facts.
Persist candidates and their stable source keys in stateRoot/candidates.json if unfinished.
This candidate queue is not authoritative task state. Do not guess missing dates or owners
beyond the configured current-user owner default. Missing assignee means owner does it.

Require affirmative user acceptance, individually or a named batch ("Accept all? [Y]").
An instruction such as "create M1: update LinkedIn and resume in this project" already
accepts that milestone. Record the instruction as the acceptance source and proceed;
ask only for material missing details. It does not accept additional tasks or other
milestones suggested by the agent. Existing project identity is reused, not duplicated.
The proposal's default selection is not acceptance. Silence, a promise found in source,
an agent's approval, or manually inserted checklist text does not create accepted work.
Save unresolved/declined dispositions so later check-ins don't re-propose unchanged items.

After acceptance use [record management](../daily-tasks-records/SKILL.md) to generate
UUIDv7 IDs, complete metadata, create files and log the accepted decision with source and
actor. Creation may be combined with explicit start/completion only if that was supplied.
Tasks require an accepted milestone; offer accepting the needed project/milestone and
tasks together rather than silently manufacturing a general project.

Return created links and the unresolved candidate count. Confirm persistence from files
and log result, not merely from the fact that the proposal was displayed.
