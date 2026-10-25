import path from 'node:path';
import { collectManagedRecords } from './navigation.mjs';
import { isUuid7 } from '../identity/identity.mjs';

const prefixes = {milestone:'m',task:'t',blocker:'b'};
const parentField = type=>type === 'task' ? 'milestone_id' : 'project_id';

/** Allocate above live labels within the parent record.
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
  const maximum = Math.max(0,...used);
  if (maximum === Number.MAX_SAFE_INTEGER) diagnostics.push({code:'numbering-exhausted',parentId,message:'No larger safe integer label is available'});
  return {type,parentId,number:diagnostics.length ? null : maximum+1,usedNumbers:[...used].sort((a,b)=>a-b),diagnostics};
}
