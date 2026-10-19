import { readFile, readdir, lstat, mkdir, writeFile, rename, unlink } from 'node:fs/promises';
import { createHash, randomUUID } from 'node:crypto';
import path from 'node:path';
import { resolveContext } from '../profile/context.mjs';
import { projectInventory, calendarDate } from '../inventory/inventory.mjs';
import { parseRecord } from '../records/records.mjs';
import { isUuid7, uuid7 } from '../identity/identity.mjs';
import { parseChecklist, planRollover } from './planning.mjs';
import { planningReview } from './review.mjs';
import { verifiedMaintenanceStatus } from './maintenance.mjs';
import { prepareTemplates } from '../templates/templates.mjs';
import { validateReviewScreen } from './screen.mjs';
import { planningOperationImpacts } from '../operations/checkpoints.mjs';
import { displayTime } from '../time/time.mjs';

const fingerprint = text => text === null ? null : createHash('sha256').update(text).digest('hex');

async function readOrdinary(filename) {
  try {
    const stat = await lstat(filename);
    if (!stat.isFile() || stat.isSymbolicLink()) throw new Error(`Expected an ordinary file: ${filename}`);
    return await readFile(filename,'utf8');
  } catch (error) { if (error.code === 'ENOENT') return null; throw error; }
}

async function stateFile(filename) {
  const text = await readOrdinary(filename);
  return {path:filename,sha256:fingerprint(text),value:text === null ? null : JSON.parse(text.replace(/^\uFEFF/,''))};
}

async function dailyPlan(context,date) {
  const filename = path.join(context.dailyPlansRoot,`${date}-daily-plan.md`);
  const markdown = await readOrdinary(filename);
  if (markdown === null) return {path:filename,date,sha256:null,id:null,proposedId:uuid7(),rows:[]};
  const record = parseRecord(markdown,filename);
  if (record.type !== 'daily-plan' || !isUuid7(record.id) || record.parse_errors.length) {
    throw new Error(`Invalid daily-plan identity or frontmatter: ${filename}`);
  }
  return {path:filename,date,sha256:fingerprint(markdown),id:record.id,rows:parseChecklist(markdown)};
}

async function names(directory) {
  try {
    if ((await lstat(directory)).isSymbolicLink()) throw new Error(`Symbolic directory excluded: ${directory}`);
    return await readdir(directory);
  } catch (error) { if (error.code === 'ENOENT') return []; throw error; }
}

async function selectedRecords(context,plans,known,sources) {
  const records = [...known], seen = new Set(known.map(record => record.id));
  const projectSources = new Set(sources.filter(source => source.anchor === 'projectsRoot').map(source => source.path));
  for (const plan of plans.filter(Boolean)) for (const row of plan.rows) {
    if (!isUuid7(row.id) || seen.has(row.id) || !row.target) continue;
    const linked = row.target.split('#')[0];
    const filename = path.resolve(path.dirname(plan.path),/\.md$/i.test(linked) ? linked : `${linked}.md`);
    const relative = path.relative(context.projectsRoot,filename);
    if (relative === '..' || relative.startsWith('..'+path.sep) || path.isAbsolute(relative)) continue;
    if (!projectSources.has(relative.split(path.sep).join('/'))) continue;
    const markdown = await readOrdinary(filename);
    if (markdown === null) continue;
    const record = parseRecord(markdown,filename);
    if (record.type !== 'task' || record.id !== row.id) continue;
    records.push(record);
    seen.add(row.id);
  }
  return records;
}

/** Prepare one bound planning screen from maintained readers; never author Markdown. */
export async function preparePlanning(input) {
  const context = await resolveContext(input);
  if (!context.configured || context.preferenceOnly) return {status:'setup-required',context};
  const templates = await prepareTemplates({...input,kinds:['dailyPlan','planDayReview']},{context});
  const today = context.localDate;
  const current = await dailyPlan(context,today);
  const rolloverState = await stateFile(path.join(context.stateRoot,'rollover',`${today}.json`));
  const reviewState = await stateFile(path.join(context.stateRoot,'review',`${today}.json`));
  const indexed = await projectInventory({...context,forceRefresh:input.forceRefresh,dryRun:input.dryRun});
  let records = indexed.inventory.tasks.map(task => ({...task,type:'task',project_id:task.projectId,milestone_id:task.milestoneId}));
  const planId = current.id ?? current.proposedId;
  let previous = null;
  let rollover = current.id ? planRollover({today,planId:current.id,userEmail:context.profile.user.email,
    currentRows:current.rows,state:rolloverState.value,records,inventory:indexed.inventory}) : {status:'missing-plan',selected:[],unresolved:[]};
  if (rollover.status === 'due' || rollover.status === 'missing-plan') {
    const dates = (await names(context.dailyPlansRoot)).map(name => /^(\d{4}\.\d{2}\.\d{2})-daily-plan\.md$/.exec(name)?.[1])
      .filter(date => calendarDate(date) && date < today).sort();
    if (dates.length) previous = await dailyPlan(context,dates.at(-1));
    records = await selectedRecords(context,[current,previous],records,indexed.inventory.sources);
    rollover = planRollover({today,planId,userEmail:context.profile.user.email,
      currentRows:current.rows,state:current.id ? rolloverState.value : null,previousDate:previous?.date,previousRows:previous?.rows ?? [],records,inventory:indexed.inventory});
  }
  else records = await selectedRecords(context,[current],records,indexed.inventory.sources);
  const sourceHashes = new Map(indexed.inventory.sources.filter(source => source.anchor === 'projectsRoot')
    .map(source => [path.resolve(context.projectsRoot,source.path),source.sha256]));
  const relevantTaskIds = new Set([
    ...current.rows.map(row => row.id),
    ...(previous?.rows ?? []).map(row => row.id),
    ...rollover.selected.map(row => row.id),
    ...records.filter(record => record.state === 'in-progress').map(record => record.id),
  ].filter(isUuid7));
  const taskSources = [];
  const seenTaskPaths = new Set();
  for (const record of records) {
    if (!relevantTaskIds.has(record.id) || !record.path) continue;
    const absolutePath = path.resolve(context.projectsRoot,record.path);
    if (seenTaskPaths.has(absolutePath)) continue;
    const sha256 = sourceHashes.get(absolutePath) ?? fingerprint(await readOrdinary(absolutePath));
    if (sha256) {
      seenTaskPaths.add(absolutePath);
      taskSources.push({path:absolutePath,sha256});
    }
  }
  rollover = {...rollover,taskSources};
  const saved = reviewState.value;
  if (saved && (saved.date !== today || saved.mappingBinding !== context.planningBinding || (saved.planId !== undefined && saved.planId !== current.id))) {
    throw new Error('Saved review belongs to another date, plan or vault; recover it before reusing numbers');
  }
  const recovery = await planningOperationImpacts(input,{context,current,previous,inventory:indexed.inventory,records,
    state:{review:reviewState,rollover:rolloverState}});
  const review = planningReview({...context,contextBinding:context.planningBinding,inventoryBinding:indexed.planningBinding,
    inventory:indexed.inventory,userEmail:context.profile.user.email,selected:rollover.selected,selectedRecords:records,
    mapping:saved?.mapping,mappingBinding:saved?.mappingBinding,position:saved?.position,page:input.page,allMilestones:input.allMilestones,recovery});
  const issuesByPath = new Map();
  for (const issue of indexed.inventory.diagnostics) {
    if (!issuesByPath.has(issue.path)) issuesByPath.set(issue.path,[]);
    issuesByPath.get(issue.path).push(issue);
  }
  return {status:recovery.blocked || rollover.status === 'conflict' ? 'recovery-required' : current.id ? 'prepared' : 'create-plan',
    displayNow:displayTime(context.now,context.timezone),
    context,current,previous,rollover,review,templates,maintenance:await verifiedMaintenanceStatus(input,indexed),
    pendingOperations:recovery.names,recovery,inventory:indexed.inventory,inventoryStatus:indexed.status,metrics:indexed.metrics,
    enrollment:indexed.inventory.diagnostics.filter(issue => issue.code === 'invalid-id').map(issue => ({path:issue.path,
      issues:issuesByPath.get(issue.path),requiresExplicitAcceptance:true})),
    inventoryHash:fingerprint(JSON.stringify({inventory:{...indexed.inventory,generatedAt:undefined},recovery:recovery.fingerprint})),reviewHash:fingerprint(JSON.stringify({review,
      templateRevision:templates.templates.planDayReview.active.revision,templateSelector:templates.templates.planDayReview.selector})),
    state:{rollover:rolloverState,review:reviewState}};
}

/** Save derived review numbers or a verified no-change completion; no generic JSON writer. */
export async function savePlanningState(input) {
  if (!['save-review','complete-rollover'].includes(input.action)) throw new TypeError('Unknown planning-state action');
  const prepared = await preparePlanning({...input,dryRun:true});
  if (!prepared.current?.id || prepared.status === 'recovery-required') throw new Error('A valid current plan and recovered operations are required');
  const {context,current,previous,rollover,review,state} = prepared;
  if (input.expectedInventoryHash !== prepared.inventoryHash ||
      (input.action === 'save-review' && input.expectedReviewHash !== prepared.reviewHash)) throw new Error('Inventory or numbered review changed; prepare again');
  if (current.rows.some(row => !isUuid7(row.id)) || new Set(current.rows.map(row => row.id)).size !== current.rows.length) throw new Error('Current plan has missing or duplicate selection identities');
  if (input.expectedPlanHash !== current.sha256 || input.expectedPreviousHash !== (previous?.sha256 ?? null)) throw new Error('Plan sources changed; prepare again');
  const target = input.action === 'save-review' ? state.review : state.rollover;
  if (!Object.hasOwn(input,'expectedStateHash') || input.expectedStateHash !== target.sha256) throw new Error('Planning state changed; prepare again');
  let value;
  if (input.action === 'save-review') {
    const validation = validateReviewScreen(input.reviewMarkdown,prepared.templates.templates.planDayReview.active,review);
    if (!validation.valid) throw new Error(`Review screen does not match the active template: ${validation.errors.join('; ')}`);
    value = {...target.value,schemaVersion:1,date:context.localDate,planId:current.id,mappingBinding:context.planningBinding,mapping:review.mapping,position:review.position,
      screen:{markdown:input.reviewMarkdown,sha256:validation.sha256,templateRevision:validation.templateRevision}};
  }
  else {
    if (rollover.status === 'complete') return {status:'unchanged',path:target.path,value:target.value};
    if (rollover.status !== 'due' || rollover.unresolved.length || rollover.own.length || rollover.delegated.length || rollover.followUp.length) {
      throw new Error('Rollover still has pending membership or unresolved references; apply and verify its operation first');
    }
    const selectedIds = new Set(current.rows.map(row => row.id));
    if (review.selected.some(row => row.suspended) || review.diagnostics.some(issue => selectedIds.has(issue.recordId) &&
        (issue.code.startsWith('invalid-') || ['missing-selected-record','selection-identity','multiple-planning-dates','view-state-difference','duplicate-id'].includes(issue.code)))) {
      throw new Error('Selected work still needs reconciliation before rollover completion');
    }
    value = {schemaVersion:1,date:context.localDate,planId:current.id,operationId:uuid7(),completedAt:context.now,
      ...(target.value?.removedIds ? {removedIds:target.value.removedIds} : {})};
  }
  if (input.dryRun) return {status:'preview',path:target.path,value};
  // Check every existing ancestor before creating script-owned state directories.
  const ancestors = [];
  for (let directory = path.dirname(target.path); ; directory = path.dirname(directory)) {
    ancestors.push(directory);
    if (directory === path.dirname(directory)) break;
  }
  for (const directory of ancestors.reverse()) {
    try { const stat = await lstat(directory); if (!stat.isDirectory() || stat.isSymbolicLink()) throw new Error(`Unsafe state directory: ${directory}`); }
    catch (error) { if (error.code !== 'ENOENT') throw error; await mkdir(directory); }
  }
  const temporary = `${target.path}.${randomUUID()}.tmp`;
  try {
    await writeFile(temporary,JSON.stringify(value,null,2)+'\n',{flag:'wx'});
    const refreshed = await preparePlanning({...input,dryRun:true,forceRefresh:true});
    if (refreshed.status === 'recovery-required' || refreshed.inventoryHash !== prepared.inventoryHash || refreshed.reviewHash !== prepared.reviewHash) {
      throw new Error('Planning dependencies or checkpoint evidence changed before save; prepare again');
    }
    if (fingerprint(await readOrdinary(target.path)) !== target.sha256 || fingerprint(await readOrdinary(current.path)) !== current.sha256 ||
        (previous && fingerprint(await readOrdinary(previous.path)) !== previous.sha256)) throw new Error('Planning sources changed before save; retry');
    await rename(temporary,target.path);
  } finally { await unlink(temporary).catch(error => { if (error.code !== 'ENOENT') throw error; }); }
  return {status:'saved',path:target.path,value};
}
