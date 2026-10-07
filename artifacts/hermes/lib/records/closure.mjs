import { validateRecords, terminal } from './validation.mjs';

/** Evaluate recorded facts only. Never infer satisfaction or mutate children. */
export function checkClosure(recordId, records) {
  const reasons = [];
  const diagnostics = validateRecords(records);
  records = records.filter(record => record && typeof record === 'object').map(record => ({...record,
    blocks:Array.isArray(record.blocks) ? record.blocks : [],
    blocked_by:Array.isArray(record.blocked_by) ? record.blocked_by : [],
    criteria:Array.isArray(record.criteria) ? record.criteria : []}));
  const matches = records.filter(record => record.id === recordId);
  if (matches.length !== 1) return {allowed:false,reasons:['Record identity is missing or duplicated']};
  const record = matches[0];
  const byId = new Map(records.map(item => [item.id,item]));
  const scope = new Set([recordId]);
  const addReason = text => { if (!reasons.includes(text)) reasons.push(text); };
  const blockers = target => {
    for (const blockerId of target.blocked_by || []) {
      const blocker = byId.get(blockerId);
      if (!blocker || blocker.type !== 'blocker') { addReason(`Missing or invalid blocker ${blockerId}`); continue; }
      scope.add(blocker.id);
      if (blocker.state !== 'resolved') addReason(`Open blocker ${blocker.id}`);
      if (!blocker.blocks?.includes(target.id)) addReason(`Blocker ${blocker.id} lacks a reciprocal reference`);
    }
    for (const blocker of records.filter(item => item.type === 'blocker' && item.blocks?.includes(target.id))) {
      scope.add(blocker.id);
      if (blocker.state !== 'resolved') addReason(`Open blocker ${blocker.id}`);
      if (!target.blocked_by?.includes(blocker.id)) addReason(`Record ${target.id} lacks a reciprocal blocker reference`);
    }
  };
  const milestone = (item, cancelled = false) => {
    scope.add(item.id);
    const children = records.filter(child => child.milestone_id === item.id);
    const tasks = children.filter(child => child.type === 'task');
    for (const task of tasks) {
      scope.add(task.id);
      if (!terminal.has(task.state)) addReason(`Unresolved task ${task.id}`);
      if (task.state !== 'cancelled' && !cancelled) blockers(task);
    }
    if (!cancelled) {
      const dods = children.filter(child => child.type === 'dod');
      if (dods.length !== 1) addReason(`Milestone ${item.id} needs exactly one Definition of Done record`);
      for (const dod of dods) {
        scope.add(dod.id);
        if (!dod.criteria.length || dod.criteria.some(criterion => criterion.checked !== true)) addReason(`Unsatisfied Definition of Done ${dod.id}`);
        blockers(dod);
      }
      blockers(item);
    }
  };
  if (record.type === 'project') {
    const milestones = records.filter(item => item.type === 'milestone' && item.project_id === record.id);
    for (const item of milestones) {
      if (!terminal.has(item.state)) addReason(`Unresolved milestone ${item.id}`);
      milestone(item, item.state === 'cancelled');
    }
    // Orphaned children cannot vanish from a closure check just because their parent is missing.
    for (const child of records.filter(item => item.project_id === record.id)) scope.add(child.id);
    blockers(record);
  } else if (record.type === 'milestone') milestone(record);
  else if (record.type === 'task') blockers(record);
  else if (record.type === 'dod') {
    if (!record.criteria?.length || record.criteria.some(item => item.checked !== true)) addReason('Definition of Done criteria are not all satisfied');
    blockers(record);
  } else if (record.type === 'blocker') addReason('Blocker resolution requires an explicit recorded condition decision');
  else addReason('Unknown record type');

  // A broken task prerequisite is informational. Every other relevant malformed
  // relationship or record must fail closed, rather than manufacture success.
  for (const issue of diagnostics) {
    if (!scope.has(issue.recordId)) continue;
    if (['unaccepted-candidate','noncanonical-filename'].includes(issue.code)) continue;
    if (['missing-reference','invalid-reference','invalid-relation'].includes(issue.code) && /^(depends_on|required_by)\b/.test(issue.message)) continue;
    addReason(`${issue.code}: ${issue.message}`);
  }
  return {allowed:reasons.length === 0,reasons};
}
