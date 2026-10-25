import path from 'node:path';
import { templateFingerprint, tableColumns } from '../templates/catalog.mjs';

const marks = {'not-started':' ','in-progress':'>',completed:'x',cancelled:'-'};
const sameColumns = (left,right) => JSON.stringify(left) === JSON.stringify(right);

function visibleLines(markdown) {
  return markdown.replaceAll('\r\n','\n').replace(/^---\n[\s\S]*?\n---(?:\n|$)/,'')
    .replace(/<!--[\s\S]*?-->/g,comment => /^<!--\s*ref:/.test(comment) ? comment : '')
    .replace(/^ {0,3}(`{3,}|~{3,})[^\n]*\n[\s\S]*?^ {0,3}\1[^\n]*(?:\n|$)/gm,'').split('\n');
}

function screenStructure(markdown) {
  const lines = visibleLines(markdown), headings = [], tables = [], rows = [];
  let table = null;
  const ancestry = [];
  for (let index = 0; index < lines.length; index++) {
    const line = lines[index];
    const heading = /^(#{1,6}) /.exec(line);
    if (heading) {
      headings.push(line.trim());
      ancestry.length = heading[1].length;
      ancestry[heading[1].length-1] = line.trim();
    }
    if (line.trim().startsWith('|') && lines[index+1]?.trim().startsWith('|')) {
      const header = tableColumns(line), separator = tableColumns(lines[index+1]);
      if (header.length === separator.length && separator.every(cell => /^:?-+:?$/.test(cell))) {
        table = header; tables.push(header); index++; continue;
      }
    }
    if (!line.trim().startsWith('|')) table = null;
    const references = [...line.matchAll(/<!--\s*ref:\s*([^>]*?)\s*-->/g)].map(match => match[1]);
    const cells = table ? tableColumns(line) : null;
    const status = (cells ? cells.map(cell => /^\[([ xX>\-])\]$/.exec(cell)).find(Boolean) : /\[([ xX>\-])\]/.exec(line))?.[1]?.toLowerCase();
    const link = /\[[^\]]+\]\([^)]+\)|\[\[[^\]]+\]\]/.test(line);
    if (!references.length && !(status !== undefined && link)) continue;
    const numberColumn = table?.findIndex(column => /^(#|No\.?|Number|Row)$/i.test(column)) ?? -1;
    rows.push({line,references,cells,table,status,link,headings:ancestry.filter(Boolean),
      number:cells ? (numberColumn >= 0 ? [Number(cells[numberColumn])] : cells.filter(cell => /^\d+$/.test(cell)).map(Number)) :
        [Number(/^\s*(?:[-*+]\s*)?(?:\[[ xX>\-]\]\s*)?(\d+)(?:[.)]|\s)/.exec(line)?.[1])]});
  }
  return {lines,headings,tables,rows};
}

function headingMatches(pattern,heading) {
  // Custom headings may contain conventional data placeholders.
  const parts = pattern.split(/(\{[^}]+\}|[A-Z][A-Z0-9]*_[A-Z0-9_]+)/);
  const expression = parts.map((part,index) => index % 2 ? '.+' : part.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')).join('');
  return new RegExp(`^${expression}$`).test(heading);
}

/** Validate agent-authored chat Markdown; never render or write a user's screen. */
export function validateReviewScreen(markdown,active,review) {
  if (typeof markdown !== 'string' || !markdown.trim()) return {valid:false,errors:['A rendered reviewMarkdown draft is required']};
  const template = screenStructure(active.content), draft = screenStructure(markdown), errors = [];
  let headingIndex = 0;
  for (const heading of template.headings) {
    while (headingIndex < draft.headings.length && !headingMatches(heading,draft.headings[headingIndex])) headingIndex++;
    if (headingIndex === draft.headings.length) errors.push(`Missing or reordered template heading: ${heading}`);
    else headingIndex++;
  }
  for (const table of draft.tables) if (!template.tables.some(expected => sameColumns(expected,table))) errors.push('Screen table columns differ from the active template');
  if (template.tables.length && draft.rows.some(row => !row.table || row.cells.length !== row.table.length)) errors.push('Task rows must use the active template tables');
  if (!template.tables.length && draft.tables.length) errors.push('The active template does not use tables');
  const expectedRows = [...review.selected,...review.available], expected = new Map(expectedRows.map(row => [row.id,row]));
  const sectionOf = row => row.headings.find(heading => /^## /.test(heading)) ?? row.headings.at(-1);
  const sections = [...new Set(template.rows.map(sectionOf).filter(Boolean))];
  // A two-section example describes selected work followed by additions. Explicit
  // SELECTED reference placeholders preserve the roles in reversed custom layouts.
  const selectedSection = sectionOf(template.rows.find(row => row.references.some(ref => /SELECTED/.test(ref))) ?? template.rows[0] ?? {headings:[]});
  const availableSection = sections.find(section => section !== selectedSection);
  const selectedIds = new Set(review.selected.map(row => row.id));
  const observed = [];
  for (const row of draft.rows) {
    if (row.references.length !== 1 || !expected.has(row.references[0])) { errors.push('Screen contains an unidentified or unexpected task row'); continue; }
    const task = expected.get(row.references[0]);
    observed.push(task.id);
    if (row.number.length !== 1 || row.number[0] !== task.number) errors.push(`Screen row number differs for ${task.id}`);
    if (sections.length === 2) {
      const section = selectedIds.has(task.id) ? selectedSection : availableSection;
      if (!row.headings.some(heading => headingMatches(section,heading))) errors.push(`Screen selection section differs for ${task.id}`);
    }
    if (!task.unresolved && row.status !== marks[task.state]) errors.push(`Screen status differs for ${task.id}`);
    if (!!task.carriedFrom !== row.line.includes('↺')) errors.push(`Screen carry provenance differs for ${task.id}`);
  }
  const observedIds = new Set(observed);
  if (observed.length !== expectedRows.length || observedIds.size !== expected.size || expectedRows.some(row => !observedIds.has(row.id))) errors.push('Screen must contain each selected and available row exactly once');
  for (const group of [review.selected,review.available]) {
    const ids = new Set(group.map(row => row.id));
    if (JSON.stringify(observed.filter(id => ids.has(id))) !== JSON.stringify([...ids])) errors.push('Screen task order differs from the prepared review');
  }
  const visible = draft.lines.join('\n');
  if (review.reviewComplete) {
    if (!/\bReview complete\b/i.test(visible)) errors.push('Completed review must show Review complete');
  } else if (review.pageCount > 0) {
    const page = /\bPage\s+(\d+)\s+of\s+(\d+)\b/i.exec(visible);
    if (!page || Number(page[1]) !== review.page + 1 || Number(page[2]) !== review.pageCount) errors.push('Screen page indicator differs from the prepared review');
  }
  for (const [label,key] of [['Open projects','openProjects'],['Open tasks','openTasks'],['Late tasks','lateTasks']]) {
    if (!active.content.includes(label)) continue;
    const value = new RegExp(`${label}:\\s*(\\d+)`).exec(visible)?.[1];
    if (value === undefined || Number(value) !== review.counts[key]) errors.push(`Screen count differs: ${label}`);
  }
  if (!draft.lines.some(line => ['[ ]','[>]','[x]','[-]'].every(mark => line.includes(mark)))) errors.push('Screen status legend is missing');
  return {valid:errors.length === 0,errors,templateRevision:templateFingerprint(active.content),sha256:templateFingerprint(markdown)};
}

/** Validate agent-authored daily plan Markdown against the active dailyPlan template. */
export function validateDailyPlan(markdown,active,options = {}) {
  if (typeof markdown !== 'string' || !markdown.trim()) return {valid:false,errors:['A rendered dailyPlan Markdown document is required']};
  const template = screenStructure(active.content), draft = screenStructure(markdown), errors = [];
  const requiredHeadings = template.headings.filter(heading => /^#{1,3} /.test(heading) && !/^## Focus\b/i.test(heading));
  let headingIndex = 0;
  for (const heading of requiredHeadings) {
    while (headingIndex < draft.headings.length && !headingMatches(heading,draft.headings[headingIndex])) headingIndex++;
    if (headingIndex === draft.headings.length) errors.push(`Missing or reordered template heading: ${heading}`);
    else headingIndex++;
  }
  const templateTaskTables = template.rows.map(row => row.table).filter(Boolean);
  for (const table of draft.tables) if (!template.tables.some(expected => sameColumns(expected,table))) errors.push('Daily plan table columns differ from the active template');
  if (templateTaskTables.length && draft.rows.some(row => !row.table || row.cells.length !== row.table.length || !templateTaskTables.some(expected => sameColumns(expected,row.table)))) {
    errors.push('Task rows must use the active dailyPlan template tables (escape wiki-link pipes as \\| inside table cells)');
  }
  if (!template.tables.length && draft.tables.length) errors.push('The active dailyPlan template does not use tables');
  const requiresGroupSubheadings = template.rows.some(row => row.headings.some(heading => /^#### /.test(heading)));
  if (requiresGroupSubheadings && draft.rows.some(row => !row.headings.some(heading => /^#### /.test(heading)))) {
    errors.push('Task rows must be grouped under #### PROJECT / MILESTONE subheadings');
  }
  const requiresWikiLink = templateTaskTables.length > 0 && /\[\[/.test(active.content);
  if (Array.isArray(options.selected)) {
    const expected = new Map(options.selected.map(row => [row.id,row]));
    const observed = [], seenNumbers = new Set();
    const hasResponsibilitySections = ['### My work','### Delegated work','### Follow-up work'].every(section => template.headings.includes(section));
    for (const row of draft.rows) {
      if (row.references.length !== 1 || !expected.has(row.references[0])) { errors.push('Daily plan contains an unidentified or unexpected task row'); continue; }
      const task = expected.get(row.references[0]);
      observed.push(task.id);
      if (row.table?.some(column => /^(#|No\.?|Number|Row)$/i.test(column))) {
        if (row.number.length !== 1 || !Number.isInteger(row.number[0]) || row.number[0] <= 0 || seenNumbers.has(row.number[0])) {
          errors.push(`Daily plan row number invalid or duplicate for ${task.id}`);
        } else seenNumbers.add(row.number[0]);
      }
      if (!task.unresolved && task.state && row.status !== marks[task.state]) errors.push(`Daily plan status differs for ${task.id}`);
      if (!task.unresolved && (requiresWikiLink ? !/\[\[[^\]]+\]\]/.test(row.line) : !row.link)) errors.push(`Daily plan task link missing for ${task.id}`);
      const carried = Boolean(task.carriedFrom || task.carried);
      if (carried !== row.line.includes('↺')) errors.push(`Daily plan carry provenance differs for ${task.id}`);
      if (hasResponsibilitySections && options.userEmail && !task.unresolved && task.owner) {
        const effectiveAssignee = task.assignee || task.owner;
        const expectedSection = effectiveAssignee === options.userEmail ? '### My work' : task.owner === options.userEmail ? '### Delegated work' : '### Follow-up work';
        if (!row.headings.some(heading => headingMatches(expectedSection,heading))) errors.push(`Daily plan responsibility section differs for ${task.id}`);
      }
    }
    const observedIds = new Set(observed);
    if (observed.length !== options.selected.length || observedIds.size !== expected.size || options.selected.some(row => !observedIds.has(row.id))) {
      errors.push('Daily plan must contain each selected task row exactly once');
    }
  }
  const visible = draft.lines.join('\n');
  for (const [label,key] of [['Open projects','openProjects'],['Open tasks','openTasks'],['Late tasks','lateTasks']]) {
    if (!active.content.includes(label)) continue;
    const value = new RegExp(`${label}:\\s*(\\d+)`).exec(visible)?.[1];
    if (value === undefined || (options.counts && Number(value) !== options.counts[key])) errors.push(`Daily plan count differs: ${label}`);
  }
  for (const meta of ['**Timezone:**','**Updated:**']) {
    if (active.content.includes(meta) && !visible.includes(meta)) errors.push(`Daily plan metadata missing: ${meta}`);
  }
  if (template.lines.some(line => ['[ ]','[>]','[x]','[-]'].every(mark => line.includes(mark))) &&
      !draft.lines.some(line => ['[ ]','[>]','[x]','[-]'].every(mark => line.includes(mark)))) {
    errors.push('Daily plan status legend is missing');
  }
  return {valid:errors.length === 0,errors,templateRevision:templateFingerprint(active.content),sha256:templateFingerprint(markdown)};
}

function buildLookup(options = {}) {
  const projectsById = new Map((options.inventory?.projects ?? []).map(p => [p.id,p]));
  const milestonesById = new Map((options.inventory?.milestones ?? []).map(m => [m.id,m]));
  const tasksById = new Map([
    ...(options.inventory?.tasks ?? []).map(t => [t.id,t]),
    ...(options.records ?? []).map(r => [r.id,r]),
  ]);
  return {
    projectsById,
    milestonesById,
    tasksById,
    projectsRoot: options.projectsRoot,
    dailyPlansRoot: options.dailyPlansRoot,
    userEmail: options.userEmail,
  };
}

function describeTaskRow(row, lookup = {}) {
  const {projectsById = new Map(), milestonesById = new Map(), tasksById = new Map(), projectsRoot, dailyPlansRoot, userEmail} = lookup;
  const task = tasksById.get(row.id) ?? row;
  const projectId = row.projectId ?? task.projectId ?? task.project_id;
  const milestoneId = row.milestoneId ?? task.milestoneId ?? task.milestone_id;
  const projectTitle = row.projectTitle ?? projectsById.get(projectId)?.title ?? 'Project';
  const milestoneTitle = row.milestoneTitle ?? milestonesById.get(milestoneId)?.title ?? 'Milestone';
  const rawTitle = (task.title && !task.title.includes('[[') ? task.title : (row.label ?? row.title ?? 'Task'))
    .replace(/^↺\s*/,'').replace(/<!--[\s\S]*?-->/g,'').replace(/\[\[(?:[^\]|\\]+\\?\|)?([^\]]+)\]\]/,'$1').trim() || 'Task';
  let relativePath = row.relativePath;
  if (!relativePath) {
    if (projectsRoot && dailyPlansRoot && task.path) {
      const absPath = path.resolve(projectsRoot,task.path);
      relativePath = path.relative(dailyPlansRoot,absPath).split(path.sep).join('/').replace(/\.md$/i,'');
    } else if (row.target) {
      relativePath = row.target.replace(/\.md$/i,'');
    } else if (task.path) {
      relativePath = String(task.path).split(path.sep).join('/').replace(/\.md$/i,'');
    } else {
      relativePath = 'task';
    }
  }
  const state = row.state ?? task.state ?? 'not-started';
  const statusMark = `[${marks[state] ?? row.mark ?? ' '}]`;
  const carried = Boolean(row.carriedFrom || row.carried);
  const owner = row.owner ?? task.owner ?? userEmail ?? '—';
  const assignee = row.assignee ?? task.assignee ?? '—';
  const dueDate = row.dueDate ?? '—';
  return {
    id: row.id,
    number: row.number,
    state,
    statusMark,
    projectTitle,
    milestoneTitle,
    title: rawTitle,
    relativePath,
    carried,
    owner,
    assignee,
    dueDate,
    unresolved: Boolean(row.unresolved),
  };
}

function renderTableCell(column, info, rowNumber, {linkTasks = false} = {}) {
  const name = column.trim();
  if (/^(#|No\.?|Number|Row)$/i.test(name)) return String(rowNumber);
  if (/^Status$/i.test(name)) return info.statusMark;
  if (/^Project$/i.test(name)) return info.projectTitle;
  if (/^Milestone$/i.test(name)) return info.milestoneTitle;
  if (/^Owner$/i.test(name)) return info.owner;
  if (/^Assignee$/i.test(name)) return info.assignee;
  if (/^(Due Date|Target Date|Due)$/i.test(name)) return info.dueDate;
  if (/^Task$/i.test(name)) {
    const label = !linkTasks || (info.unresolved && !info.relativePath) ? info.title : `[[${info.relativePath}\\|${info.title}]]`;
    return `${info.carried ? '↺ ' : ''}${label} <!-- ref: ${info.id} -->`;
  }
  return '—';
}

/** Propose a template-conforming chat review screen draft from prepared review data. */
export function draftReviewScreen(active, review, options = {}) {
  const template = screenStructure(active.content);
  const lookup = buildLookup(options);
  const sectionOf = row => row.headings.find(heading => /^## /.test(heading)) ?? row.headings.at(-1);
  const sections = [...new Set(template.rows.map(sectionOf).filter(Boolean))];
  const selectedSection = sectionOf(template.rows.find(row => row.references.some(ref => /SELECTED/.test(ref))) ?? template.rows[0] ?? {headings:[]})
    ?? template.headings.find(h => /^## /.test(h)) ?? '## Already selected';
  const availableSection = sections.find(section => section !== selectedSection)
    ?? template.headings.filter(h => /^## /.test(h))[1] ?? '## Available tasks';
  const tableHeader = template.tables[0] ?? null;
  const renderRows = (rows, emptyText) => {
    if (!rows.length) return emptyText;
    if (!tableHeader) {
      return rows.map((row, idx) => {
        const info = describeTaskRow(row, lookup);
        return `- ${info.number ?? idx + 1}. ${info.statusMark} ${info.carried ? '↺ ' : ''}${info.title} <!-- ref: ${info.id} -->`;
      }).join('\n');
    }
    const headerLine = `| ${tableHeader.join(' | ')} |`;
    const sepLine = `| ${tableHeader.map(() => '---').join(' | ')} |`;
    const bodyLines = rows.map((row, idx) => {
      const info = describeTaskRow(row, lookup);
      return `| ${tableHeader.map(col => renderTableCell(col, info, info.number ?? idx + 1, {linkTasks: false})).join(' | ')} |`;
    });
    return [headerLine, sepLine, ...bodyLines].join('\n');
  };
  const blocks = [];
  const countLabels = [['Open projects','openProjects'],['Open tasks','openTasks'],['Late tasks','lateTasks']]
    .filter(([label]) => active.content.includes(label));
  if (countLabels.length && review.counts) {
    blocks.push(countLabels.map(([label,key]) => `${label}: ${review.counts[key] ?? 0}`).join('          '));
  }
  if (review.reviewComplete) {
    blocks.push('Review complete');
  } else if (review.pageCount > 0) {
    blocks.push(`Page ${review.page + 1} of ${review.pageCount}`);
  }
  if (options.firstRunToday && /This is your first check-in today\./.test(active.content)) {
    blocks.push('This is your first check-in today. Review the work carried forward, then choose which available tasks to add. Status marks show progress; the sections indicate whether work is selected for today. [x] means completed, never merely selected.');
  }
  const legendLine = template.lines.find(line => ['[ ]','[>]','[x]','[-]'].every(mark => line.includes(mark)))
    ?? 'Legend: [ ] not started · [>] in progress · [x] completed · [-] cancelled · ↺ carried forward';
  let legendPlaced = false;
  const visibleTemplate = template.lines.join('\n');
  for (const heading of template.headings) {
    if (heading === selectedSection) {
      blocks.push(heading, renderRows(review.selected ?? [], 'No tasks currently selected for today.'));
    } else if (heading === availableSection) {
      blocks.push(heading, renderRows(review.available ?? [], 'No additional available tasks on this page.'), legendLine);
      legendPlaced = true;
    } else if (/^## /.test(heading)) {
      const escaped = heading.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const tailMatch = new RegExp(`^${escaped}\\s*\\n([\\s\\S]*?)(?=^#{1,6} |$)`, 'm').exec(visibleTemplate);
      const tail = tailMatch?.[1]?.trim() || 'Reply with an explicit instruction and the item numbers (for example: "Add 2, 3 to today", "Keep the current selections", or "Next page").';
      blocks.push(heading, tail);
    } else {
      blocks.push(heading);
    }
  }
  if (!template.headings.includes(selectedSection)) {
    blocks.push(selectedSection, renderRows(review.selected ?? [], 'No tasks currently selected for today.'));
  }
  if (!template.headings.includes(availableSection)) {
    blocks.push(availableSection, renderRows(review.available ?? [], 'No additional available tasks on this page.'));
  }
  if (!legendPlaced) blocks.push(legendLine);
  return blocks.filter(Boolean).join('\n\n') + '\n';
}

function extractExistingSection(markdown, heading) {
  if (typeof markdown !== 'string' || !markdown.trim()) return null;
  const escaped = heading.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const match = new RegExp(`^${escaped}\\s*\\n([\\s\\S]*?)(?=^#{1,3} |$)`, 'm').exec(markdown.replaceAll('\r\n','\n'));
  const body = match?.[1]?.trim();
  if (!body || /FOCUS_DESCRIPTION|BLOCKER_TITLE|BLOCKER_OWNER_NAME/.test(body)) return null;
  return body;
}

/** Propose a template-conforming daily plan Markdown draft from prepared planning data. */
export function draftDailyPlan(active, options = {}) {
  const {
    id,
    date = '1970.01.01',
    timezone = 'UTC',
    createdAt = '1970-01-01T00:00:00.000Z',
    now = createdAt,
    displayNow = `${date} 00:00 ${timezone}`,
    counts = {openProjects:0,openTasks:0,lateTasks:0},
    selected = [],
    userEmail = '',
    existingMarkdown = null,
  } = options;
  const template = screenStructure(active.content);
  const lookup = buildLookup(options);
  const tableHeader = template.rows.map(row => row.table).find(Boolean) ?? template.tables[0] ?? null;
  const requiresGroupSubheadings = template.rows.some(row => row.headings.some(heading => /^#### /.test(heading)));
  const usedNumbers = new Set();
  let nextSeq = 1;
  const enriched = selected.map(row => {
    const info = describeTaskRow(row, lookup);
    let num = Number.isInteger(info.number) && info.number > 0 && !usedNumbers.has(info.number) ? info.number : null;
    if (num === null) {
      while (usedNumbers.has(nextSeq)) nextSeq++;
      num = nextSeq++;
    }
    usedNumbers.add(num);
    return {...info, number: num, raw: row};
  });
  const own = [], delegated = [], followUp = [];
  for (const item of enriched) {
    const effectiveAssignee = item.assignee !== '—' ? item.assignee : item.owner;
    if (item.unresolved || !userEmail || effectiveAssignee === userEmail) own.push(item);
    else if (item.owner === userEmail) delegated.push(item);
    else followUp.push(item);
  }
  const renderSectionItems = items => {
    if (!items.length) return 'No work selected for this section.';
    if (!tableHeader) {
      return items.map(info => `- ${info.statusMark} ${info.carried ? '↺ ' : ''}[[${info.relativePath}|${info.title}]] <!-- ref: ${info.id} -->`).join('\n');
    }
    const headerLine = `| ${tableHeader.join(' | ')} |`;
    const sepLine = `| ${tableHeader.map(() => '---').join(' | ')} |`;
    if (!requiresGroupSubheadings) {
      const bodyLines = items.map(info => `| ${tableHeader.map(col => renderTableCell(col, info, info.number, {linkTasks: true})).join(' | ')} |`);
      return [headerLine, sepLine, ...bodyLines].join('\n');
    }
    const groups = new Map();
    for (const info of items) {
      const key = `${info.projectTitle} / ${info.milestoneTitle}`;
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(info);
    }
    const groupBlocks = [];
    for (const [groupKey, groupItems] of groups.entries()) {
      const bodyLines = groupItems.map(info => `| ${tableHeader.map(col => renderTableCell(col, info, info.number, {linkTasks: true})).join(' | ')} |`);
      groupBlocks.push(`#### ${groupKey}\n\n${[headerLine, sepLine, ...bodyLines].join('\n')}`);
    }
    return groupBlocks.join('\n\n');
  };
  const frontmatter = [
    '---',
    `id: ${id}`,
    'type: daily-plan',
    `title: "Daily plan ${date}"`,
    'document-maturity: reviewed',
    `timezone: "${timezone}"`,
    `created_at: "${createdAt}"`,
    `updated_at: "${now}"`,
    '---',
  ].join('\n');
  const requiredHeadings = template.headings.filter(heading => /^#{1,3} /.test(heading) && !/^## Focus\b/i.test(heading));
  const titleHeading = (requiredHeadings.find(h => /^# /.test(h)) ?? `# Daily plan — ${date}`).replace(/LOCAL_DATE|\{[^}]+\}/g, date);
  const blocks = [titleHeading];
  const countLabels = [['Open projects','openProjects'],['Open tasks','openTasks'],['Late tasks','lateTasks']]
    .filter(([label]) => active.content.includes(label));
  if (countLabels.length) {
    blocks.push(countLabels.map(([label,key]) => `${label}: ${counts[key] ?? 0}`).join('          '));
  }
  const metaLines = [];
  if (active.content.includes('**Timezone:**')) metaLines.push(`**Timezone:** ${timezone}  `);
  if (active.content.includes('**Updated:**')) metaLines.push(`**Updated:** ${displayNow}`);
  if (metaLines.length) blocks.push(metaLines.join('\n'));
  const existingFocus = extractExistingSection(existingMarkdown, '## Focus');
  if (existingFocus) blocks.push('## Focus', existingFocus);
  const legendLine = template.lines.find(line => ['[ ]','[>]','[x]','[-]'].every(mark => line.includes(mark)));
  let legendPlaced = false;
  for (const heading of requiredHeadings) {
    if (/^# /.test(heading)) continue;
    if (/^## Selected for today\b/i.test(heading)) {
      blocks.push(heading);
    } else if (/^#{2,3} My work\b/i.test(heading)) {
      blocks.push(heading, renderSectionItems(own));
    } else if (/^#{2,3} Delegated work\b/i.test(heading)) {
      blocks.push(heading, renderSectionItems(delegated));
    } else if (/^#{2,3} Follow-up work\b/i.test(heading)) {
      blocks.push(heading, renderSectionItems(followUp));
      if (legendLine) {
        blocks.push(legendLine);
        legendPlaced = true;
      }
    } else if (/^## Blockers\b/i.test(heading)) {
      blocks.push(heading, extractExistingSection(existingMarkdown, heading) ?? 'No active blockers.');
    } else if (/^## Decisions\b/i.test(heading)) {
      blocks.push(heading, extractExistingSection(existingMarkdown, heading) ?? 'No decisions recorded.');
    } else if (/^## Notes\b/i.test(heading)) {
      blocks.push(heading, extractExistingSection(existingMarkdown, heading) ?? 'No additional notes.');
    } else {
      blocks.push(heading, extractExistingSection(existingMarkdown, heading) ?? 'None.');
    }
  }
  if (!requiredHeadings.some(h => /^#{2,3} (?:My|Delegated|Follow-up) work\b/i.test(h)) && enriched.length) {
    blocks.push(renderSectionItems(enriched));
  }
  if (legendLine && !legendPlaced) blocks.push(legendLine);
  return `${frontmatter}\n${blocks.join('\n\n')}\n`;
}
