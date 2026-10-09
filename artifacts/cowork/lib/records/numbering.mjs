import path from 'node:path';
import { collectManagedRecords } from './navigation.mjs';
import { queryDecisions } from '../log/decision-log.mjs';
import { isUuid7 } from '../identity/identity.mjs';
import { recordDirectoryIsHoldingArea } from './parse.mjs';

const prefixes = {milestone:'m',task:'t',blocker:'b'};
const parentField = type=>type === 'task' ? 'milestone_id' : 'project_id';
function snapshots(value) {
  if (Array.isArray(value)) return value.filter(record=>record && typeof record === 'object' && !Array.isArray(record));
  if (Array.isArray(value?.records)) return snapshots(value.records);
  if (value && typeof value === 'object' && typeof value.path === 'string') return [value];
  if (value && typeof value === 'object' && isUuid7(value.id)) return [value];
  return [];
}

function artifactOnly(entry,projectsRoot) {
  const explicitArtifact = /^artifact\.(?:moved|renamed|deleted|retired)$/i.test(entry.action);
  if (!explicitArtifact && !/(?:mov|renam|delet|retir)/i.test(entry.action)) return false;
  const before = snapshots(entry.before);
  const after = snapshots(entry.after);
  if (!before.length || /(?:mov|renam)/i.test(entry.action) && !after.length) return false;
  return [...before,...after].every(record=>{
    if (['id','type','project_id','milestone_id','record_version'].some(key=>Object.hasOwn(record,key)) ||
        typeof record.path !== 'string' || !record.path.trim()) return false;
    const relative = path.relative(projectsRoot,path.resolve(projectsRoot,record.path));
    if (relative === '..' || relative.startsWith(`..${path.sep}`) || path.isAbsolute(relative)) return explicitArtifact && path.isAbsolute(record.path);
    const parts = relative.split(path.sep);
    if (parts.some(part=>part.startsWith('.'))) return false;
    return parts.slice(0,-1).some((_,index)=>recordDirectoryIsHoldingArea(parts.slice(0,index+1).join(path.sep)));
  });
}

// Corrections enrich missing numbering facts; they cannot erase a known identity,
// parent, path or version. All descendants must cover exactly the root's affected IDs.
function correctedSnapshots(entries) {
  const ids = entries[0].record_ids;
  const sides = {before:new Map(),after:new Map()};
  let consistent = true;
  for (const entry of entries) {
    if (entry.record_ids.length !== ids.length || entry.record_ids.some(id=>!ids.includes(id))) consistent = false;
    for (const side of ['before','after']) {
      for (const record of snapshots(entry[side])) {
        if (side === 'before' && Object.hasOwn(record,'snapshot_kind') && record.snapshot_kind !== 'observed') consistent = false;
        const id = record.id ?? (ids.length === 1 ? ids[0] : undefined);
        if (!isUuid7(id) || !ids.includes(id)) { consistent = false; continue; }
        const merged = sides[side].get(id) ?? {id};
        for (const key of ['id','type','path','project_id','milestone_id','record_version']) {
          if (!Object.hasOwn(record,key)) continue;
          if (Object.hasOwn(merged,key) && merged[key] !== record[key]) consistent = false;
          else merged[key] = record[key];
        }
        sides[side].set(id,merged);
      }
    }
  }
  const concrete = record=>isUuid7(record.id) && typeof record.path === 'string' && record.path.length > 0 &&
    (record.type === 'project' && !/^[mtb]\d/i.test(path.basename(record.path)) ||
      record.type === 'dod' && isUuid7(record.milestone_id) && !/^[mtb]\d/i.test(path.basename(record.path)) ||
      Object.hasOwn(prefixes,record.type) && isUuid7(record[parentField(record.type)]));
  const before = [...sides.before.values()];
  const after = [...sides.after.values()];
  const needsAfter = /(?:mov|renam)/i.test(entries[0].action);
  const acceptsNewRecords = entries[0].action === 'task.cancel-and-accept';
  // A batch can retire an existing record and create another: the newly created
  // record has only an after snapshot, but still contributes its allocated label.
  const complete = consistent && ids.length > 0 && before.length > 0 &&
    ids.every(id=>sides.before.has(id) || acceptsNewRecords && sides.after.has(id)) &&
    (!needsAfter || ids.every(id=>sides.before.has(id) && sides.after.has(id))) && [...before,...after].every(concrete);
  return {complete,before,after};
}

/** Allocate above live and concrete historical labels; ambiguous history blocks allocation.
 * Historical snapshots use {id,type,path,project_id,milestone_id} directly, in
 * arrays, or under records. Exact append-only corrections can enrich missing facts.
 * This is a proposal, not a reservation: callers must recheck before creating files.
 */
export async function nextRecordNumber(input) {
  const {type,parentId,projectsRoot} = input;
  if (!Object.hasOwn(prefixes,type) || !isUuid7(parentId)) throw new TypeError('Expected milestone/task/blocker type and UUIDv7 parentId');
  const records = await collectManagedRecords(projectsRoot);
  const diagnostics = [];
  const used = new Set();
  const liveLabels = new Map();
  const parent = records.filter(record=>record.id === parentId);
  if (parent.length !== 1 || parent[0].type !== (type === 'task' ? 'milestone' : 'project')) {
    diagnostics.push({code:'invalid-numbering-parent',parentId,message:'Parent must resolve to exactly one record of the expected type'});
  }
  function collect(record,source) {
    if (record.type !== type || record[parentField(type)] !== parentId) return;
    const label = /^([mtb])([1-9]\d*)-/i.exec(path.basename(record.path ?? ''));
    const number = Number(label?.[2]);
    // Unversioned legacy records can receive their first label during migration.
    // A numeric-looking filename is evidence of a label even when malformed.
    if (!label && record.record_version === undefined &&
        !/^[mtb]\d/i.test(path.basename(record.path ?? '')) && isUuid7(record.id) &&
        !(record.parse_errors?.length)) return;
    if (!label || label[1].toLowerCase() !== prefixes[type] || !Number.isSafeInteger(number)) {
      diagnostics.push({code:'invalid-numbering-label',source,recordId:record.id,message:'Record has no valid parent-local numeric label'});
    } else used.add(number);
  }
  for (const record of records) {
    const label = /^([mtb])([1-9]\d*)-/i.exec(path.basename(record.path));
    if (label?.[1].toLowerCase() === prefixes[type] && (!record.type || !isUuid7(record[parentField(type)]))) {
      diagnostics.push({code:'invalid-numbering-record',source:record.path,message:'Numbered record lacks a concrete type or parent identity'});
    }
    collect(record,record.path);
    if (record.type === type && record[parentField(type)] === parentId && label) {
      if (liveLabels.has(label[2])) diagnostics.push({code:'duplicate-numbering-label',source:record.path,message:'Two live records share a parent-local numeric label'});
      liveLabels.set(label[2],record.path);
    }
  }
  const entries = [];
  let offset = 0;
  do {
    const result = await queryDecisions({projectsRoot,offset,limit:1000,dryRun:true});
    entries.push(...result.entries);
    offset = result.nextOffset;
  } while (offset !== null);
  const byId = new Map(entries.map(entry=>[entry.id,entry]));
  const groups = new Map();
  for (const entry of entries) {
    // Keep every known historical number, even if a later correction conflicts.
    for (const record of [...snapshots(entry.before),...snapshots(entry.after)]) {
      if (typeof record.path === 'string') collect(record,entry.id);
    }
    let root = entry;
    const seen = new Set();
    while (root.corrects && !seen.has(root.id)) {
      seen.add(root.id);
      root = byId.get(root.corrects);
    }
    if (seen.has(root.id)) {
      diagnostics.push({code:'history-numbering-ambiguous',source:entry.id,message:'Correction chain is cyclic'});
      continue;
    }
    if (!groups.has(root.id)) groups.set(root.id,[]);
    groups.get(root.id).push(entry);
  }
  for (const group of groups.values()) {
    // Locate the original independently of file/page order; the log API validates linkage.
    const original = group.find(entry=>!entry.corrects);
    const ordered = [original,...group.filter(entry=>entry !== original)];
    if (/(?:selection|deselection|plan\.)/i.test(original.action) || !/(?:mov|renam|retir|delet|cancel|migrat)/i.test(original.action)) continue;
    if (group.length === 1 && artifactOnly(original,projectsRoot)) continue;
    const resolved = correctedSnapshots(ordered);
    for (const record of [...resolved.before,...resolved.after]) collect(record,original.id);
    if (!resolved.complete) diagnostics.push({code:'history-numbering-ambiguous',source:original.id,message:'Historical label-changing event lacks consistent concrete identity, type, parent and path snapshots covering affected records'});
  }
  const maximum = Math.max(0,...used);
  if (maximum === Number.MAX_SAFE_INTEGER) diagnostics.push({code:'numbering-exhausted',parentId,message:'No larger safe integer label is available'});
  return {type,parentId,number:diagnostics.length ? null : maximum+1,usedNumbers:[...used].sort((a,b)=>a-b),diagnostics};
}
