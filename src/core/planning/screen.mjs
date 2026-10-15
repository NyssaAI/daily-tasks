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
    if (!task.unresolved && !row.link) errors.push(`Screen task link missing for ${task.id}`);
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
