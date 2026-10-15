import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

const templateDefinitions = {
  dailyPlan: {file: 'daily-plan.md', contract: 'daily-plan-v1'},
  planDayReview: {file: 'plan-day-select-tasks-screen.md', contract: 'review-v1'},
  projectIndex: {file: 'project-index.md', contract: 'project-v1'},
  milestone: {file: 'milestone.md', contract: 'milestone-v2'},
  task: {file: 'task.md', contract: 'task-v2'}
};

export const templateKinds = Object.freeze(Object.keys(templateDefinitions));
export const templateFiles = Object.freeze(Object.fromEntries(Object.entries(templateDefinitions).map(([kind,value]) => [kind,value.file])));

export function templateFingerprint(text) {
  return `sha256:${createHash('sha256').update(text.replaceAll('\r\n', '\n')).digest('hex')}`;
}

function verifyFingerprint(kind, entry) {
  if (typeof entry.content !== 'string' || entry.revision !== templateFingerprint(entry.content)) {
    throw new Error(`Template fingerprint mismatch for ${kind}.`);
  }
}

export async function loadTemplateCatalog() {
  const history = JSON.parse(await readFile(new URL('./history.json', import.meta.url), 'utf8'));
  return Object.fromEntries(await Promise.all(templateKinds.map(async kind => {
    const definition = templateDefinitions[kind];
    const path = fileURLToPath(new URL(`../../../skills/daily-tasks/assets/${definition.file}`, import.meta.url));
    const content = await readFile(path, 'utf8');
    const revisions = history.templates[kind];
    for (const entry of revisions) verifyFingerprint(kind, entry);
    return [kind, {
      kind, revision: templateFingerprint(content), content, contract: definition.contract,
      source: 'bundled', path, history: revisions
    }];
  })));
}

export function identifyTemplate(kind, content, catalog) {
  const bundled = catalog[kind];
  if (!templateKinds.includes(kind) || !bundled) throw new Error(`Unknown template kind: ${kind}`);
  verifyFingerprint(kind, bundled);
  for (const entry of bundled.history ?? []) verifyFingerprint(kind, entry);
  const revision = templateFingerprint(content);
  if (revision === bundled.revision) {
    return {kind, source: 'bundled', recognized: true, revision, contract: bundled.contract};
  }
  const historical = bundled.history?.find(entry => entry.revision === revision);
  if (historical) {
    return {
      kind, source: 'bundled-copy', recognized: true, revision,
      contract: historical.contract, provenance: historical.provenance
    };
  }
  return {kind, source: 'custom', recognized: false, revision, contract: null};
}

function templateLayout(content) {
  const visible = content.replaceAll('\r\n', '\n')
    .replace(/^---\n[\s\S]*?\n---(?:\n|$)/, '')
    .replace(/<!--[\s\S]*?-->/g, '')
    .replace(/^ {0,3}(`{3,}|~{3,})[^\n]*\n[\s\S]*?^ {0,3}\1[ \t]*$/gm, '');
  const lines = visible.split('\n');
  const headings = [...new Set(lines.filter(line => /^#{1,6} /.test(line)).map(line => line.trim()))];
  const tables = [];
  for (let index = 0; index < lines.length - 1; index++) {
    if (!lines[index].trim().startsWith('|')) continue;
    const separator = tableColumns(lines[index + 1]);
    const columns = tableColumns(lines[index]);
    if (separator.length === columns.length && separator.every(cell => /^:?-+:?$/.test(cell))) {
      if (!tables.some(table => JSON.stringify(table) === JSON.stringify(columns))) tables.push(columns);
    }
  }
  const checklists = /^\s*[-*+]\s+\[[ x>\-]\]/m.test(visible);
  const layout = tables.length ? (checklists ? 'tables and checklists' : 'tables') : (checklists ? 'checklists' : 'prose');
  return {headings, tables, layout};
}

export function tableColumns(line) {
  return line.trim().replace(/^\|/, '').replace(/\|$/, '').split(/(?<!\\)\|/).map(cell => cell.trim());
}

export function compareTemplates(activeContent, candidateContent) {
  const active = templateLayout(activeContent);
  const candidate = templateLayout(candidateContent);
  const changed = templateFingerprint(activeContent) !== templateFingerprint(candidateContent);
  const headings = {
    added: candidate.headings.filter(heading => !active.headings.includes(heading)),
    removed: active.headings.filter(heading => !candidate.headings.includes(heading))
  };
  const tables = {
    added: candidate.tables.filter(columns => !active.tables.some(table => JSON.stringify(table) === JSON.stringify(columns))),
    removed: active.tables.filter(columns => !candidate.tables.some(table => JSON.stringify(table) === JSON.stringify(columns)))
  };
  const activeColumns = [...new Set(active.tables.flat())];
  const candidateColumns = [...new Set(candidate.tables.flat())];
  const columns = {
    added: candidateColumns.filter(column => !activeColumns.includes(column)),
    removed: activeColumns.filter(column => !candidateColumns.includes(column))
  };
  const layout = {before: active.layout, after: candidate.layout};
  const summary = [];
  if (layout.before !== layout.after) summary.push(`Layout changes from ${layout.before} to ${layout.after}.`);
  if (headings.added.length) summary.push(`Added headings: ${headings.added.join(', ')}.`);
  if (headings.removed.length) summary.push(`Removed headings: ${headings.removed.join(', ')}.`);
  if (columns.added.length) summary.push(`Added table columns: ${columns.added.join(', ')}.`);
  if (columns.removed.length) summary.push(`Removed table columns: ${columns.removed.join(', ')}.`);
  if (!columns.added.length && !columns.removed.length && (tables.added.length || tables.removed.length)) {
    summary.push('Table column order or arrangement changed.');
  }
  if (!summary.length) summary.push(changed ? 'Template text changed; headings and table layout are unchanged.' : 'No template changes.');
  return {changed, headings, tables, columns, layout, summary};
}
