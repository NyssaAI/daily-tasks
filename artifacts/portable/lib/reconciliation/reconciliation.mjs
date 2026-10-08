import { isDeepStrictEqual as equal } from 'node:util';
import { isUuid7 } from '../identity/identity.mjs';
import { utcTimestamp } from '../time/time.mjs';

const operationalStates = new Set(['not-started','in-progress','completed','cancelled']);
const optionalFields = new Set(['assignee','started_at','resolved_at','target_date']);
const snapshot = value => value === undefined ? {present:false} : {present:true,value:structuredClone(value)};
function validSnapshot(value) {
  return value && typeof value === 'object' && !Array.isArray(value) &&
    (value.present === false ? Object.keys(value).length === 1 :
      value.present === true && Object.keys(value).length === 2 && Object.hasOwn(value,'value') && value.value !== undefined);
}

function translate(view, base, current) {
  const result = {...view};
  for (const field of optionalFields) if (result[field] === null) result[field] = undefined;
  if (Object.hasOwn(result,'checked')) {
    if (typeof result.checked !== 'boolean') throw new TypeError('checked must be boolean');
    if (base.type === 'dod') throw new TypeError('Reconcile individual DoD criteria, not a document completion checkbox');
    const done = base.type === 'blocker' ? 'resolved' : 'completed';
    const baselineChecked = base.state === done;
    if (result.state !== undefined) {
      if (result.checked !== (result.state === done)) throw new TypeError('Checkbox and state disagree within a view');
    } else if (result.checked !== baselineChecked) {
      const reopened = base.type === 'blocker' ? 'open' : ((current.started_at || base.started_at) ? 'in-progress' : 'not-started');
      const translated = result.checked ? done : reopened;
      result.state = translated;
    }
    delete result.checked;
  }
  return result;
}

function invalidField(field, value, record) {
  if (optionalFields.has(field) && value === undefined) return;
  if (field === 'type' && value !== record.type) return 'Record type cannot change through a view';
  if (field === 'owner' && (typeof value !== 'string' || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value))) return 'Owner requires a human email';
  if (field === 'assignee' && (typeof value !== 'string' || !value.trim())) return 'Assignee requires a human email or stable agent name';
  if (field === 'state' && !(record.type === 'blocker' ? ['open','resolved'].includes(value) : operationalStates.has(value))) return 'Invalid type-specific state';
  if (['created_at','updated_at','started_at','resolved_at','target_date'].includes(field)) {
    try { utcTimestamp(value); } catch { return 'Expected valid GMT timestamp'; }
  }
  if (['project_id','milestone_id'].includes(field) && !isUuid7(value)) return 'Parent requires UUIDv7';
}

/** Three-way, field-wise comparison. Returned changes are proposals, not authorized writes. */
export function reconcileRecord(base, current, views) {
  if (!base || !current || !isUuid7(base.id) || base.id !== current.id || !Array.isArray(views)) throw new TypeError('Matching UUIDv7 baseline/current and views array are required');
  const sources = views.map(view => {
    if (!view || view.id !== base.id) throw new TypeError('View identity does not match record');
    return translate(view,base,current);
  });
  const record = structuredClone(current);
  const conflicts = [];
  const changes = [];
  const fields = new Set(sources.flatMap(source => Object.keys(source)));
  for (const field of fields) {
    if (field === 'id') continue;
    const proposals = [];
    if (!equal(current[field],base[field])) proposals.push({source:'current',value:current[field]});
    sources.forEach((source,index) => {
      if (Object.hasOwn(source,field) && !equal(source[field],base[field])) proposals.push({source:`view:${index}`,value:source[field]});
    });
    const distinct = [];
    for (const proposal of proposals) if (!distinct.some(value => equal(value,proposal.value))) distinct.push(proposal.value);
    if (distinct.length > 1) {
      conflicts.push({field,base:base[field],current:current[field],proposals});
      continue;
    }
    if (distinct.length === 1 && !equal(distinct[0],current[field])) {
      const reason = invalidField(field,distinct[0],current);
      if (reason) {
        conflicts.push({field,base:base[field],current:current[field],proposals,reason});
        continue;
      }
      if (distinct[0] === undefined) delete record[field];
      else record[field] = structuredClone(distinct[0]);
      changes.push({field,before:snapshot(current[field]),after:snapshot(distinct[0])});
    }
  }
  if (changes.some(change => change.field === 'state') && ['not-started','in-progress','open'].includes(record.state) && record.resolved_at !== undefined) {
    changes.push({field:'resolved_at',before:snapshot(record.resolved_at),after:snapshot(undefined)});
    delete record.resolved_at;
  }
  return {record,conflicts,changes};
}

/** Return reopening proposals; only a task's own unsatisfied criteria reopen that task. */
export function reopenAncestors(records, changedIds) {
  const cloned = structuredClone(records);
  const byId = new Map();
  for (const record of cloned) byId.set(record.id,byId.has(record.id) ? null : record);
  const lookup = id => {
    const record = byId.get(id);
    if (record === null) throw new TypeError(`Duplicate record identity ${id} must be resolved first`);
    if (!record) throw new TypeError(`Missing referenced record ${id}`);
    return record;
  };
  const changed = new Set();
  const visiting = new Set();
  const reopen = id => {
    if (!id || visiting.has(id)) return;
    visiting.add(id);
    const record = lookup(id);
    if (['project','milestone'].includes(record.type) && record.state === 'completed') {
      record.state = 'in-progress';
      delete record.resolved_at;
      changed.add(id);
    }
    if (record.milestone_id) reopen(record.milestone_id);
    if (record.project_id) reopen(record.project_id);
  };
  for (const id of changedIds) {
    const record = lookup(id);
    if (record.type === 'blocker' && record.state === 'open') {
      const targets = new Set([...(record.blocks || []),...cloned.filter(item => item.blocked_by?.includes(id)).map(item => item.id)]);
      for (const target of targets) reopen(target);
    } else if (['task','milestone'].includes(record.type) && record.state !== 'cancelled' &&
      ((record.record_version === '2' || record.dod_section === true) && !record.criteria?.length || record.criteria?.some(item => !item.checked))) {
      if (record.type === 'task' && record.state === 'completed') {
        record.state = record.started_at ? 'in-progress' : 'not-started';
        delete record.resolved_at;
        changed.add(record.id);
      }
      reopen(record.id);
    } else if ((record.type === 'dod' && record.criteria?.some(item => !item.checked)) ||
      (['task','milestone'].includes(record.type) && !['completed','cancelled'].includes(record.state))) {
      if (record.milestone_id) reopen(record.milestone_id);
      if (record.project_id) reopen(record.project_id);
    }
  }
  return {records:cloned,changedIds:[...changed]};
}

/** Recovery is value-based and side-effect free, with all intent supplied by caller. */
export function recoverOperation(operation, actual) {
  if (!operation || !Array.isArray(operation.changes) || !operation.changes.length || !actual || typeof actual !== 'object') throw new TypeError('Expected operation changes and actual values');
  const pending = [];
  const conflicts = [];
  const seen = new Set();
  for (const change of operation.changes) {
    if (!change || typeof change.key !== 'string' || seen.has(change.key) || !validSnapshot(change.before) || !validSnapshot(change.after)) throw new TypeError('Each recovery change needs a unique key and explicit before/after presence snapshots');
    seen.add(change.key);
    const value = snapshot(Object.hasOwn(actual,change.key) ? actual[change.key] : undefined);
    if (equal(value,change.after)) continue;
    if (equal(value,change.before)) pending.push(structuredClone(change));
    else conflicts.push({key:change.key,before:change.before,after:change.after,actual:value});
  }
  return {status:conflicts.length ? 'conflict' : pending.length ? 'pending' : 'already-applied',pending,conflicts};
}
