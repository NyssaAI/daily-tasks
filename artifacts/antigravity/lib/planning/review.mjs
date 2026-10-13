import path from 'node:path';
import { localDay, utcTimestamp } from '../time/time.mjs';
import { calendarDate, taskSummary } from '../inventory/inventory.mjs';
import { isUuid7 } from '../identity/identity.mjs';
import { recordIssueIsInvalid } from '../records/records.mjs';
import { assertPlanningScope } from '../profile/context.mjs';

const unfinished = state => ['not-started','in-progress'].includes(state);

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
  const pending = new Set(input.pendingFutureIds ?? []);
  const openTasks = inventory.tasks.filter(t => t.state === 'not-started' &&
    !pending.has(t.id) && !t.planned.some(p => p.date > today));
  const mapping = {...input.mapping};
  const numbers = Object.values(mapping);
  if (numbers.some(n => !Number.isSafeInteger(n) || n < 1) || new Set(numbers).size !== numbers.length) throw new TypeError('Mapping needs unique positive row numbers');
  let next = Math.max(0,...numbers) + 1;
  const number = id => mapping[id] ?? (mapping[id] = next++);
  const row = (task,extra={}) => ({...task,...extra,number:number(task.id),dueDate:task.targetDate ? localDay(task.targetDate,input.timezone) : null});
  const selectedIds = new Set(selected.map(r => r.id));
  for (const task of inventory.tasks) if (unfinished(task.state) && task.planned.some(p => p.date === today)) selectedIds.add(task.id);
  const selectedRows = [...selectedIds].map(id => {
    const task = tasks.get(id), source = selectedById.get(id);
    if (!task) { diagnostics.push({code:'missing-selected-record',recordId:id,message:'Retain unresolved selected row until reconciled'}); return {...source,id,number:number(id),unresolved:true}; }
    return row(task,source?.carriedFrom ? {carriedFrom:source.carriedFrom} : {});
  }).filter(Boolean);
  const first = new Map();
  const openMilestones = new Set(inventory.milestones.filter(m => unfinished(m.state)).map(m => m.id));
  for (const m of inventory.milestones) if (!first.has(m.projectId) && unfinished(m.state)) first.set(m.projectId,m.id);
  const unsafeProjects = new Set(inventory.milestones.filter(m => excluded.has(m.id)).map(m => m.projectId));
  for (const issue of diagnostics) if (issue.code === 'invalid-planning-scope') unsafeProjects.add(issue.projectId);
  const additions = unknownAllocation ? [] : openTasks.filter(t => !selectedIds.has(t.id) && !excluded.has(t.id) && !unsafeProjects.has(t.projectId) &&
    openMilestones.has(t.milestoneId) && t.milestoneId === first.get(t.projectId));
  // Assign all eligible handles before pagination so Show more cannot renumber earlier rows.
  const numbered = additions.map(t => row(t));
  const projectPages = new Map();
  for (const task of numbered) {
    if (!projectPages.has(task.projectId)) projectPages.set(task.projectId,[]);
    projectPages.get(task.projectId).push(task);
  }
  const pages = [...projectPages.values()];
  const projectIds = [...projectPages.keys()];
  const savedPosition = input.position;
  let page = input.page;
  if (page === undefined) {
    page = 0;
    if (savedPosition?.complete) page = pages.length;
    else if (savedPosition?.projectId) {
      page = projectIds.indexOf(savedPosition.projectId);
      if (page < 0) {
        const previousIds = savedPosition.projectIds ?? [];
        const previousIndex = previousIds.indexOf(savedPosition.projectId);
        const nextId = previousIndex < 0 ? undefined : previousIds.slice(previousIndex + 1).find(id => projectPages.has(id));
        page = nextId === undefined ? pages.length : projectIds.indexOf(nextId);
      }
    }
  }
  if (!Number.isSafeInteger(page) || page < 0) throw new TypeError('page must be a nonnegative integer');
  page = Math.min(page,pages.length);
  const reviewComplete = page === pages.length;
  const position = {projectId:projectIds[page] ?? null,page,projectIds,complete:reviewComplete};
  const openProjectIds = new Set(openTasks.map(task => task.projectId));
  return {today,counts:{openProjects:inventory.projects.filter(p => unfinished(p.state) && openProjectIds.has(p.id)).length,
    openTasks:openTasks.length,lateTasks:openTasks.filter(t => t.targetDate && localDay(t.targetDate,input.timezone) < today).length},
    selected:selectedRows,available:pages[page] ?? [],hasMore:page + 1 < pages.length,page,pageCount:pages.length,position,reviewComplete,mapping,
    outOfViewSelectedIds:[],diagnostics,mappingBinding:input.contextBinding,incomplete:diagnostics.some(d => d.code !== 'noncanonical-filename')};
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
    if (!isUuid7(id) || !task || !unfinished(task.state) || ambiguous) { conflicts.push({id,reason:'missing-invalid-or-ambiguous-task'}); continue; }
    if (action === 'remove' && task.state === 'in-progress') { conflicts.push({id,reason:'in-progress-requires-reschedule-or-closure'}); continue; }
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
