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
