import path from 'node:path';
import { localDay, utcTimestamp } from '../time/time.mjs';
import { calendarDate, taskSummary } from '../inventory/inventory.mjs';
import { isUuid7 } from '../identity/identity.mjs';
import { recordIssueIsInvalid } from '../records/records.mjs';
import { assertPlanningScope } from '../profile/context.mjs';

const open = state => ['not-started','in-progress'].includes(state);

/** Derived screen data only; no Markdown writes and no implicit task/day selection. */
export function planningReview(input) {
  if (input.contextBinding !== undefined || input.inventoryBinding !== undefined) assertPlanningScope(input);
  const {inventory,userEmail} = input;
  const today = localDay(input.now ?? new Date().toISOString(),input.timezone);
  if (inventory?.schemaVersion !== 1 || !userEmail) throw new TypeError('Inventory v1 and userEmail required');
  const selected = input.selected ?? [];
  const tasks = new Map(inventory.tasks.map(t => [t.id,t]));
  for (const record of input.selectedRecords ?? []) if (!tasks.has(record.id)) tasks.set(record.id,taskSummary(record));
  const selectedById = new Map();
  for (const row of selected) if (!selectedById.has(row.id)) selectedById.set(row.id,row);
  const diagnostics = [...inventory.diagnostics];
  const excluded = new Set(diagnostics.filter(d => recordIssueIsInvalid(d) || ['multiple-planning-dates','selection-identity','missing-order','duplicate-selection','view-state-difference'].includes(d.code)).map(d => d.recordId));
  const unknownAllocation = diagnostics.some(d => d.code === 'selection-identity' && !d.recordId);
  const owned = inventory.tasks.filter(t => t.owner === userEmail && open(t.state));
  const mapping = {...input.mapping};
  const numbers = Object.values(mapping);
  if (numbers.some(n => !Number.isSafeInteger(n) || n < 1) || new Set(numbers).size !== numbers.length) throw new TypeError('Mapping needs unique positive row numbers');
  let next = Math.max(0,...numbers) + 1;
  const number = id => mapping[id] ?? (mapping[id] = next++);
  const row = (task,extra={}) => ({...task,...extra,number:number(task.id),dueDate:task.targetDate ? localDay(task.targetDate,input.timezone) : null});
  const selectedIds = new Set(selected.map(r => r.id));
  for (const task of owned) if (task.planned.some(p => p.date === today)) selectedIds.add(task.id);
  const outOfViewSelectedIds = [];
  const selectedRows = [...selectedIds].map(id => {
    const task = tasks.get(id), source = selectedById.get(id);
    if (!task) { diagnostics.push({code:'missing-selected-record',recordId:id,message:'Retain unresolved selected row until reconciled'}); return {...source,id,number:number(id),unresolved:true}; }
    if (task.owner !== userEmail) { outOfViewSelectedIds.push(id); return null; }
    return row(task,source?.carriedFrom ? {carriedFrom:source.carriedFrom} : {});
  }).filter(Boolean);
  const first = new Map();
  const openMilestones = new Set(inventory.milestones.filter(m => open(m.state)).map(m => m.id));
  for (const m of inventory.milestones) if (!first.has(m.projectId) && open(m.state)) first.set(m.projectId,m.id);
  const unsafeProjects = new Set(inventory.milestones.filter(m => excluded.has(m.id)).map(m => m.projectId));
  for (const issue of diagnostics) if (issue.code === 'invalid-planning-scope') unsafeProjects.add(issue.projectId);
  const pending = new Set(input.pendingFutureIds ?? []);
  const additions = unknownAllocation ? [] : owned.filter(t => !selectedIds.has(t.id) && !excluded.has(t.id) && !unsafeProjects.has(t.projectId) &&
    !pending.has(t.id) && !t.planned.some(p => p.date > today) && openMilestones.has(t.milestoneId) && (input.allMilestones || t.milestoneId === first.get(t.projectId)));
  // Assign all eligible handles before slicing so Show more cannot renumber earlier rows.
  const numbered = additions.map(t => row(t));
  const page = input.page ?? 0;
  if (!Number.isSafeInteger(page) || page < 0) throw new TypeError('page must be a nonnegative integer');
  return {today,counts:{openProjects:inventory.projects.filter(p => p.owner === userEmail && open(p.state)).length,
    openTasks:owned.length,lateTasks:owned.filter(t => t.targetDate && localDay(t.targetDate,input.timezone) < today).length},
    selected:selectedRows,available:numbered.slice(page*15,page*15+15),hasMore:numbered.length > (page+1)*15,mapping,
    outOfViewSelectedIds,diagnostics,mappingBinding:input.contextBinding,incomplete:diagnostics.some(d => d.code !== 'noncanonical-filename')};
}

/** Resolve already-explicit planning instructions into checkpoint effects for the skill. */
export function planSelection(input) {
  if (input.contextBinding !== undefined || input.inventoryBinding !== undefined) assertPlanningScope(input);
  const {inventory,taskIds,action,date,today,dailyPlansRoot} = input;
  if (!['add','move','remove'].includes(action) || !Array.isArray(taskIds) || !calendarDate(today) ||
      (action !== 'remove' && (!calendarDate(date) || date < today)) || !path.isAbsolute(dailyPlansRoot ?? '')) throw new TypeError('Explicit action, taskIds, current/future date and absolute dailyPlansRoot required');
  const effects = [], conflicts = [];
  const tasks = new Map(inventory.tasks.map(t => [t.id,t]));
  const ambiguousIds = new Set(inventory.diagnostics.filter(d => ['multiple-planning-dates','selection-identity','duplicate-selection','view-state-difference'].includes(d.code)).map(d => d.recordId));
  const unsafeProjects = new Set(inventory.diagnostics.filter(d => d.code === 'invalid-planning-scope').map(d => d.projectId));
  for (const id of new Set(taskIds)) {
    const task = tasks.get(id);
    const ambiguous = ambiguousIds.has(id) || ambiguousIds.has(undefined);
    if (!isUuid7(id) || !task || !open(task.state) || ambiguous) { conflicts.push({id,reason:'missing-invalid-or-ambiguous-task'}); continue; }
    if (action !== 'remove' && unsafeProjects.has(task.projectId)) { conflicts.push({id,reason:'invalid-project-scope'}); continue; }
    const active = task.planned.filter(p => p.date >= today);
    if (active.length > 1 || (action === 'add' && active[0] && active[0].date !== date)) { conflicts.push({id,reason:'already-planned-on-another-date',planned:active}); continue; }
    if (action === 'remove' && active[0] && active[0].date !== (date ?? today)) { conflicts.push({id,reason:'selection-date-changed',planned:active}); continue; }
    if (action !== 'remove' && active[0]?.date === date) continue;
    if (action === 'remove' && !active.length) continue;
    effects.push({id,from:active[0] ?? null,to:action === 'remove' ? null : {date,path:path.join(dailyPlansRoot,`${date}-daily-plan.md`),createIfMissing:true},preserveHistory:true});
  }
  return {effects,conflicts};
}

export function maintenanceStatus(input) {
  const now = utcTimestamp(input.now ?? new Date().toISOString());
  let age = NaN;
  try { age = Date.parse(now) - Date.parse(utcTimestamp(input.lastFullReconcileAt)); } catch { /* Absent/invalid success evidence is due. */ }
  return {fullReconcileDue:!(age >= 0 && age < 14400*1000),preferredModel:'gpt-6-luna',
    alwaysCheck:['current-plan-edits','previous-plan-edits','applicable-pending-operations']};
}
