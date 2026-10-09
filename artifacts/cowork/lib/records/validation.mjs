import { isUuid7 } from '../identity/identity.mjs';
import { utcTimestamp } from '../time/time.mjs';

export const terminal = new Set(['completed','cancelled']);
export const types = new Set(['project','milestone','task','blocker','dod']);
const states = new Set(['not-started','in-progress',...terminal]);
const relationTypes = {depends_on:['task'],required_by:['task'],blocks:['project','milestone','task','dod'],blocked_by:['blocker']};
export const diagnostic = (record, code, message, extra = {}) =>
  ({code, recordId:record?.id, path:record?.path, message, ...extra});

/** Invalid source facts block their planning scope; naming advice does not hide work. */
export const recordIssueIsInvalid = issue => issue.code.startsWith('invalid-') ||
  ['duplicate-id','missing-title'].includes(issue.code) ||
  (issue.code === 'missing-reference' && /^(project_id|milestone_id)\b/.test(issue.message));

function filenameIssue(record) {
  if (typeof record.path !== 'string') return null;
  const filename = record.path.split(/[\\/]/).at(-1);
  const stem = filename.replace(/\.md$/i,'');
  const descriptiveTask = record.type !== 'task' ||
    (/\p{L}/u.test(stem) && !['task','untitled','new-task'].includes(stem.toLowerCase()));
  const reserved = value => /^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)/i.test(value);
  if (record.record_version === '2' && ['milestone','task','blocker'].includes(record.type) &&
      !(record.type === 'blocker' ? /^b[1-9]\d*-[\p{L}\p{N}]+(?:-[\p{L}\p{N}]+)*\.md$/u : record.type === 'milestone' ? /^m[1-9]\d*-[\p{L}\p{N}]+(?:-[\p{L}\p{N}]+)*\.md$/u : /^t[1-9]\d*-[\p{L}\p{N}]+(?:-[\p{L}\p{N}]+)*\.md$/u).test(filename)) {
    return diagnostic(record,'noncanonical-filename','Use m{number}-{name}.md for milestones, t{number}-{name}.md for tasks and b{number}-{name}.md for blockers; allocate an unused parent-local number through the move protocol');
  }
  if (filename === filename.toLowerCase() && filename.endsWith('.md') &&
      /^[\p{L}\p{N}]+(?:[.-][\p{L}\p{N}]+)*\.md$/u.test(filename) && descriptiveTask && !reserved(stem)) return null;
  const taskSlug = typeof record.title === 'string' ? record.title.normalize('NFKC').toLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu,'-').replace(/^-|-$/g,'') : '';
  const recordKind = types.has(record.type) ? record.type : 'record';
  const suggestedStem = (record.type === 'task' && taskSlug ? taskSlug : stem.toLowerCase().replace(/[^\p{L}\p{N}.-]+/gu,'-')) || recordKind;
  return diagnostic(record,'noncanonical-filename','Use a lowercase descriptive filename and .md extension; rename only through the record move protocol',
    {suggestedFilename:`${reserved(suggestedStem) ? `${recordKind}-` : ''}${suggestedStem}.md`});
}

/** Metadata checks describe consistency, not proof of human authorization. */
export function validateRecords(records) {
  if (!Array.isArray(records)) throw new TypeError('Records must be an array');
  const diagnostics = [];
  const index = new Map();
  const identities = new Map();
  const numbers = new Map();
  const emit = (record, code, message) => diagnostics.push(diagnostic(record,code,message));
  const addIdentity = (id, record, label) => {
    if (!isUuid7(id)) { emit(record,'invalid-id', `${label} requires UUIDv7`); return; }
    const previous = identities.get(id);
    if (previous) {
      emit(record,'duplicate-id', `${label} duplicates ${id}`);
      emit(previous,'duplicate-id', `Identity ${id} appears more than once`);
    } else identities.set(id,record);
  };
  for (const record of records) {
    if (!record || typeof record !== 'object') { emit(record,'invalid-record','Expected a record object'); continue; }
    addIdentity(record.id,record,'Record');
    if (isUuid7(record.id)) index.set(record.id,record);
    const naming = filenameIssue(record);
    if (naming) diagnostics.push(naming);
    if (!types.has(record.type)) emit(record,'invalid-type','Unknown record type');
    if (record.record_version !== undefined && record.record_version !== '2') emit(record,'invalid-version','Unsupported record_version; expected scalar 2');
    if (['milestone','task','blocker'].includes(record.type)) {
      const label = /^(m|t|b)([1-9]\d*)-/i.exec(record.path?.split(/[\\/]/).at(-1) ?? '');
      if (label && label[1].toLowerCase() === (record.type === 'blocker' ? 'b' : record.type === 'task' ? 't' : 'm')) {
        const key = `${record.type}:${record.type === 'task' ? record.milestone_id : record.project_id}:${label[2]}`;
        const previous = numbers.get(key);
        if (previous) { emit(record,'invalid-number','Duplicate number within parent'); emit(previous,'invalid-number','Duplicate number within parent'); }
        else numbers.set(key,record);
      }
    }
    if (typeof record.title !== 'string' || !record.title.trim()) emit(record,'missing-title','Title is required');
    if (typeof record.owner !== 'string' || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(record.owner)) emit(record,'invalid-owner','Owner must be a human email address');
    if (record.assignee !== undefined && (typeof record.assignee !== 'string' || !record.assignee.trim())) emit(record,'invalid-assignee','Assignee must be a human email or stable agent name');
    if (record.type === 'blocker' ? !['open','resolved'].includes(record.state)
      : record.type !== 'dod' && !states.has(record.state)) emit(record,'invalid-state','Invalid type-specific state');
    for (const field of ['created_at','updated_at','started_at','resolved_at','target_date']) {
      if (!['created_at','updated_at'].includes(field) && record[field] === undefined) continue;
      try { utcTimestamp(record[field]); } catch { emit(record,'invalid-time',`${field} must be a valid GMT timestamp`); }
    }
    for (const message of Array.isArray(record.parse_errors) ? record.parse_errors : []) emit(record,'invalid-frontmatter',message);
    if (record.criteria !== undefined && !Array.isArray(record.criteria)) emit(record,'invalid-criterion','criteria must be an array');
    for (const criterion of Array.isArray(record.criteria) ? record.criteria : []) {
      addIdentity(criterion?.id,record,'DoD criterion');
      if (typeof criterion?.checked !== 'boolean' || typeof criterion?.text !== 'string' || !criterion.text.trim()) emit(record,'invalid-criterion','DoD criterion requires text and a checked boolean');
    }
    if (!['dod','milestone','task'].includes(record.type) && record.criteria?.length) emit(record,'invalid-criterion','Only tasks, milestones and legacy DoD records hold criteria');
    if (record.refs !== undefined && !Array.isArray(record.refs)) emit(record,'invalid-reference','refs must be an array');
    for (const reference of Array.isArray(record.refs) ? record.refs : []) {
      if (!isUuid7(reference?.id)) emit(record,'invalid-reference','Wiki link requires an adjacent UUIDv7 ref');
      if (typeof reference?.target !== 'string' || !reference.target.trim()) emit(record,'invalid-reference','Wiki link requires a target');
    }
  }
  for (const record of records.filter(r => r && typeof r === 'object')) {
    if (record.projections !== undefined && !Array.isArray(record.projections)) emit(record,'invalid-reference','projections must be an array');
    for (const projection of Array.isArray(record.projections) ? record.projections : []) {
      if (projection?.id === undefined) emit(record,'unaccepted-candidate','Manual checklist row requires acceptance and task creation');
      else if (!isUuid7(projection.id)) emit(record,'invalid-reference','Projection requires UUIDv7 ref');
      else if (!identities.has(projection.id)) emit(record,'missing-reference',`Projection points to missing identity ${projection.id}`);
    }
    for (const reference of Array.isArray(record.refs) ? record.refs : []) {
      if (isUuid7(reference?.id) && !identities.has(reference.id)) emit(record,'missing-reference',`${reference.relation || 'Wiki link'} points to missing record ${reference.id}`);
    }
    for (const [field, expected] of Object.entries(relationTypes)) {
      if (record[field] !== undefined && !Array.isArray(record[field])) { emit(record,'invalid-relation',`${field} must be an array`); continue; }
      for (const id of record[field] || []) {
        if (!isUuid7(id)) emit(record,'invalid-reference',`${field} contains a non-UUIDv7 reference`);
        const target = index.get(id);
        if (!target) emit(record,'missing-reference',`${field} points to missing record ${id}`);
        else if (!expected.includes(target.type) || (['depends_on','required_by'].includes(field) && record.type !== 'task') || (field === 'blocks' && record.type !== 'blocker')) emit(record,'invalid-relation',`${field} has incompatible record types`);
        if (id === record.id) emit(record,'invalid-relation',`${field} cannot reference itself`);
      }
    }
    for (const [field,type] of [['project_id','project'],['milestone_id','milestone']]) {
      const required = field === 'milestone_id' ? ['task','dod'].includes(record.type) : ['milestone','task','dod'].includes(record.type);
      if (record[field] === undefined && !required) continue;
      if (!isUuid7(record[field])) { emit(record,'invalid-parent',`${field} requires a UUIDv7 parent`); continue; }
      const parent = index.get(record[field]);
      if (!parent) emit(record,'missing-reference',`${field} points to a missing parent`);
      else if (parent.type !== type) emit(record,'invalid-parent',`${field} points to the wrong record type`);
    }
    const milestone = isUuid7(record.milestone_id) ? index.get(record.milestone_id) : undefined;
    if (milestone && record.project_id !== milestone.project_id) emit(record,'invalid-parent','Task/DoD project does not match its milestone');
  }
  return diagnostics;
}
