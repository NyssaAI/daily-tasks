import { isUuid7 } from '../identity/identity.mjs';
import { parseViewRows } from '../records/views.mjs';
import { calendarDate } from '../inventory/inventory.mjs';
import { utcTimestamp } from '../time/time.mjs';
import { recordIssueIsInvalid } from '../records/records.mjs';

// Pure selection support: it does not choose work, assign dates, or write files.
export function carryForward(previousRows, records, userEmail, options = {}) {
  if (options.inventory && !calendarDate(options.today)) throw new TypeError('today is required with inventory');
  const byId = new Map();
  const duplicateIds = new Set();
  for (const record of records) {
    if (byId.has(record.id)) duplicateIds.add(record.id);
    byId.set(record.id, record);
  }
  const seen = new Set();
  const inventoryTasks = new Map((options.inventory?.tasks ?? []).map(task => [task.id,task]));
  const ambiguousIds = new Set((options.inventory?.diagnostics ?? []).filter(d => d.code === 'selection-identity').map(d => d.recordId));
  const multipleDates = new Set((options.inventory?.diagnostics ?? []).filter(d => d.code === 'multiple-planning-dates').map(d => d.recordId));
  const changedViews = new Set((options.inventory?.diagnostics ?? []).filter(d => ['view-state-difference','duplicate-selection'].includes(d.code)).map(d => d.recordId));
  const invalidIds = new Set((options.inventory?.diagnostics ?? []).filter(recordIssueIsInvalid).map(d => d.recordId));
  const result = { own: [], delegated: [], unresolved: [] };
  for (const row of previousRows) {
    if (!isUuid7(row.id)) { result.unresolved.push({ ...row, reason: 'missing-identity' }); continue; }
    if (seen.has(row.id) || row.selected === false) continue;
    seen.add(row.id);
    const record = byId.get(row.id);
    if (duplicateIds.has(row.id) || !record) {
      result.unresolved.push({ ...row, reason: duplicateIds.has(row.id) ? 'duplicate-identity' : 'missing-record' }); continue;
    }
    if (['completed', 'cancelled'].includes(record.state)) continue;
    if (invalidIds.has(row.id) || !['not-started','in-progress'].includes(record.state)) {
      result.unresolved.push({...row,reason:'invalid-record'}); continue;
    }
    const task = inventoryTasks.get(row.id);
    if (ambiguousIds.has(undefined) || ambiguousIds.has(row.id)) {
      result.unresolved.push({...row,reason:'ambiguous-active-selection'}); continue;
    }
    if (changedViews.has(row.id)) {
      result.unresolved.push({...row,reason:'view-needs-reconciliation'}); continue;
    }
    if (task?.planned.some(p => p.date > options.today)) continue;
    if (multipleDates.has(row.id)) {
      result.unresolved.push({...row,reason:'multiple-planning-dates'}); continue;
    }
    const effectiveAssignee = record.assignee || record.owner;
    if (effectiveAssignee === userEmail) result.own.push({ ...row, selected: true });
    else if (record.owner === userEmail) result.delegated.push({ ...row, selected: true });
    else result.unresolved.push({ ...row, reason: 'outside-user-responsibility' });
  }
  return result;
}

/** Propose once-per-day rollover into any current plan; the skill persists and verifies it. */
export function planRollover(input) {
  const {today,planId,previousDate,records = [],userEmail,inventory,state} = input;
  const currentRows = input.currentRows ?? [], previousRows = input.previousRows ?? [];
  if (!calendarDate(today) || !isUuid7(planId) || !userEmail || !Array.isArray(currentRows) ||
      !Array.isArray(previousRows) || !Array.isArray(records) ||
      (input.removedIds !== undefined && (!Array.isArray(input.removedIds) || !input.removedIds.every(isUuid7))) ||
      (previousDate !== undefined && (!calendarDate(previousDate) || previousDate >= today)) ||
      (previousRows.length && previousDate === undefined)) throw new TypeError('Current date, plan UUID, userEmail and valid earlier-plan rows required');
  if (state !== undefined && state !== null) {
    const validState = state.schemaVersion === 1 && state.date === today && state.planId === planId &&
      (state.removedIds === undefined || (Array.isArray(state.removedIds) && state.removedIds.every(isUuid7)));
    let validCompletion = false;
    try { validCompletion = isUuid7(state.operationId) && !!utcTimestamp(state.completedAt); }
    catch { /* Corrupt completion evidence must not reintroduce removed selections. */ }
    if (!validState || (Object.hasOwn(state,'completedAt') && !validCompletion)) {
      return {status:'conflict',selected:currentRows,own:[],delegated:[],unresolved:[{reason:'invalid-rollover-state'}]};
    }
    if (validCompletion) return {status:'complete',selected:currentRows,own:[],delegated:[],unresolved:[]};
  }
  // Existing membership (including an explicit selected:false removal) wins over carry.
  const retainedIds = new Set([...currentRows.map(row => row.id).filter(isUuid7),...(input.removedIds ?? []),...(state?.removedIds ?? [])]);
  const carry = carryForward(previousRows.filter(row => !retainedIds.has(row.id)),records,userEmail,{inventory,today});
  const carried = rows => rows.map(row => ({...row,carriedFrom:previousDate}));
  const own = carried(carry.own), delegated = carried(carry.delegated);
  const unresolved = carried(carry.unresolved);
  return {status:'due',selected:[...currentRows.filter(row => row.selected !== false),...own,...delegated,...unresolved],
    own,delegated,unresolved};
}

export function parseChecklist(markdown) {
  return parseViewRows(markdown).filter(row => row.mark !== undefined);
}
