import { isUuid7 } from '../identity/identity.mjs';
import { utcTimestamp } from '../time/time.mjs';

export const terminal = new Set(['completed','cancelled']);
export const types = new Set(['project','milestone','task','blocker','dod']);
const states = new Set(['not-started','in-progress',...terminal]);
const relationTypes = {depends_on:['task'],required_by:['task'],blocks:['project','milestone','task','dod'],blocked_by:['blocker']};
export const diagnostic = (record, code, message, extra = {}) =>
  ({code, recordId:record?.id, path:record?.path, message, ...extra});

/** Metadata checks describe consistency, not proof of human authorization. */
export function validateRecords(records) {
  if (!Array.isArray(records)) throw new TypeError('Records must be an array');
  const diagnostics = [];
  const index = new Map();
  const identities = new Map();
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
    index.set(record.id,record);
    if (!types.has(record.type)) emit(record,'invalid-type','Unknown record type');
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
    if (record.type !== 'dod' && record.criteria?.length) emit(record,'invalid-criterion','Only milestone DoD records hold criteria');
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
    const milestone = index.get(record.milestone_id);
    if (milestone && record.project_id !== milestone.project_id) emit(record,'invalid-parent','Task/DoD project does not match its milestone');
  }
  return diagnostics;
}
