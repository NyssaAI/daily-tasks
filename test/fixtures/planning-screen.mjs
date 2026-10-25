// Synthetic agent-authored chat draft used at the planning-state boundary.
export function planningScreen(packet) {
  const counts = packet.review.counts;
  const table = rows => rows.length ? [
    '| # | Status | Project | Milestone | Task | Owner | Assignee | Due Date |',
    '| --- | --- | --- | --- | --- | --- | --- | --- |',
    ...rows.map(row => `| ${row.number} | ${{'not-started':'[ ]','in-progress':'[>]','completed':'[x]','cancelled':'[-]'}[row.state] ?? '[ ]'} | Project | Milestone | ${row.carriedFrom ? '↺ ' : ''}[${row.title ?? 'Unresolved'}](task.md) <!-- ref: ${row.id} --> | ${row.owner ?? '—'} | ${row.assignee ?? '—'} | ${row.dueDate ?? '—'} |`)
  ].join('\n') : 'No tasks.';
  return `Open projects: ${counts.openProjects}          Open tasks: ${counts.openTasks}          Late tasks: ${counts.lateTasks}

${packet.review.reviewComplete ? 'Review complete' : packet.review.pageCount > 0 ? `Page ${packet.review.page + 1} of ${packet.review.pageCount}` : ''}

## Already selected

${table(packet.review.selected)}

## Available tasks

${table(packet.review.available)}

Legend: [ ] not started · [>] in progress · [x] completed · [-] cancelled · ↺ carried forward

## Update your plan

Reply by row number and symbol or description. Add tasks, keep selections, or show details.
`;
}

// Synthetic agent-authored daily plan Markdown matching the bundled dailyPlan template.
export function dailyPlanDocument({id,date = '2026.10.13',timezone = 'UTC',now = '2026-10-13T14:00:00Z',displayNow = '2026.10.13 14:00 UTC',counts = {openProjects:1,openTasks:1,lateTasks:0},selected = [],userEmail = 'owner@example.test'}) {
  const table = rows => rows.length ? [
    '#### Project / Milestone',
    '',
    '| # | Status | Project | Milestone | Task | Due Date |',
    '| --- | --- | --- | --- | --- | --- |',
    ...rows.map((row,index) => `| ${row.number ?? index + 1} | ${{'not-started':'[ ]','in-progress':'[>]','completed':'[x]','cancelled':'[-]'}[row.state] ?? '[ ]'} | Project | Milestone | ${row.carriedFrom || row.carried ? '↺ ' : ''}[[../projects/task\\|${row.title ?? 'Task'}]] <!-- ref: ${row.id} --> | ${row.dueDate ?? '—'} |`),
  ].join('\n') : 'No work selected for this section.';
  const own = selected.filter(row => (row.assignee || row.owner || userEmail) === userEmail);
  const delegated = selected.filter(row => (row.assignee || row.owner || userEmail) !== userEmail && (row.owner || userEmail) === userEmail);
  const followUp = selected.filter(row => (row.assignee || row.owner || userEmail) !== userEmail && (row.owner || userEmail) !== userEmail);
  return `---
id: ${id}
type: daily-plan
title: "Daily plan ${date}"
document-maturity: reviewed
timezone: "${timezone}"
created_at: "${now}"
updated_at: "${now}"
---
# Daily plan — ${date}

Open projects: ${counts.openProjects}          Open tasks: ${counts.openTasks}          Late tasks: ${counts.lateTasks}

**Timezone:** ${timezone}  
**Updated:** ${displayNow}

## Selected for today

### My work

${table(own)}

### Delegated work

${table(delegated)}

### Follow-up work

${table(followUp)}

Legend: [ ] not started · [>] in progress · [x] completed · [-] cancelled · ↺ carried forward

## Blockers

No active blockers.

## Decisions

No decisions recorded.

## Notes and references

No additional notes.
`;
}
