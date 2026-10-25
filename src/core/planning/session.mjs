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
import { validateReviewScreen, validateDailyPlan, draftReviewScreen, draftDailyPlan } from './screen.mjs';
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
  const result = {path:filename,sha256:fingerprint(text),value:text === null ? null : JSON.parse(text.replace(/^\uFEFF/,''))};
  Object.defineProperty(result,'text',{value:text,enumerable:false});
  return result;
}

async function dailyPlan(context,date) {
  const filename = path.join(context.dailyPlansRoot,`${date}-daily-plan.md`);
  const markdown = await readOrdinary(filename);
  if (markdown === null) return {plan:{path:filename,date,sha256:null,id:null,proposedId:uuid7(),rows:[]},markdown:null,record:null};
  const record = parseRecord(markdown,filename);
  if (record.type !== 'daily-plan' || !isUuid7(record.id) || record.parse_errors.length) {
    throw new Error(`Invalid daily-plan identity or frontmatter: ${filename}`);
  }
  return {plan:{path:filename,date,sha256:fingerprint(markdown),id:record.id,rows:parseChecklist(markdown)},markdown,record};
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
  const currentLoaded = await dailyPlan(context,today);
  const current = currentLoaded.plan;
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
    if (dates.length) previous = (await dailyPlan(context,dates.at(-1))).plan;
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
  if (currentLoaded.markdown !== null) {
    const planValidation = validateDailyPlan(currentLoaded.markdown,templates.templates.dailyPlan.active,{
      selected:review.selected,
      counts:review.counts,
      userEmail:context.profile.user.email,
    });
    current.templateValidation = {valid:planValidation.valid,errors:planValidation.errors,templateRevision:planValidation.templateRevision};
    Object.defineProperty(current,'hasTemplateMetadata',{value:Boolean(currentLoaded.record?.timezone || /^# Daily plan\b/m.test(currentLoaded.markdown)),enumerable:false});
  }
  const issuesByPath = new Map();
  for (const issue of indexed.inventory.diagnostics) {
    if (!issuesByPath.has(issue.path)) issuesByPath.set(issue.path,[]);
    issuesByPath.get(issue.path).push(issue);
  }
  const displayNow = displayTime(context.now,context.timezone);
  const inventoryHash = fingerprint(JSON.stringify({inventory:{...indexed.inventory,generatedAt:undefined},recovery:recovery.fingerprint}));
  const reviewHash = fingerprint(JSON.stringify({review,
    templateRevision:templates.templates.planDayReview.active.revision,templateSelector:templates.templates.planDayReview.selector}));
  const dailyPlanMarkdown = draftDailyPlan(templates.templates.dailyPlan.active,{
    id:planId,
    date:today,
    timezone:context.timezone,
    createdAt:currentLoaded.record?.created_at ?? context.now,
    now:context.now,
    displayNow,
    counts:review.counts,
    selected:review.selected,
    userEmail:context.profile.user.email,
    existingMarkdown:currentLoaded.markdown,
    inventory:indexed.inventory,
    records,
    projectsRoot:context.projectsRoot,
    dailyPlansRoot:context.dailyPlansRoot,
  });
  const dailyPlanSha256 = fingerprint(dailyPlanMarkdown);
  const reviewMarkdown = draftReviewScreen(templates.templates.planDayReview.active,review,{
    inventory:indexed.inventory,
    records,
    projectsRoot:context.projectsRoot,
    dailyPlansRoot:context.dailyPlansRoot,
    userEmail:context.profile.user.email,
    firstRunToday:rollover.status !== 'complete' && reviewState.sha256 === null,
  });
  const sharedStateInput = {
    vaultRoot:context.vaultRoot,
    configurationSources:context.configurationSources,
    stateRoot:context.stateRoot,
    homeRoot:context.homeRoot,
    preferenceOverrides:context.preferenceOverrides,
    now:context.now,
    ...(input.page !== undefined ? {page:input.page} : {}),
    ...(input.allMilestones !== undefined ? {allMilestones:input.allMilestones} : {}),
  };
  const needsRolloverWrite = !current.id ||
    (rollover.status === 'due' && Boolean(rollover.own.length || rollover.delegated.length || rollover.followUp.length || rollover.unresolved.length));
  let rolloverOperation = null;
  if (needsRolloverWrite && !recovery.blocked && rollover.status !== 'conflict') {
    const operationId = uuid7();
    const operationPath = path.join(context.stateRoot,'operations',`${operationId}.json`);
    const expectedSelectedIds = rollover.selected.filter(row => row.selected !== false && isUuid7(row.id)).map(row => row.id);
    rolloverOperation = {
      operationId,
      operationPath,
      planPath:current.path,
      dailyPlanMarkdown,
      checkpoint:{
        schemaVersion:2,
        operation_id:operationId,
        contextBinding:context.planningBinding,
        event:{
          id:uuid7(),
          operation_id:operationId,
          action:'plan.rollover',
          record_ids:[planId,...expectedSelectedIds],
          actor:{kind:'person',id:context.profile.user.email},
          activity_at:context.now,
          recorded_at:context.now,
          time_defaulted:false,
          original_words:typeof input.originalWords === 'string' && input.originalWords.trim() ? input.originalWords.trim() : 'Plan the day rollover',
          after:{date:today,selected_ids:expectedSelectedIds},
        },
        files:[{path:current.path,before:current.sha256,after:dailyPlanSha256}],
        rollover:{
          date:today,
          planId,
          previousPlanId:previous?.id ?? null,
          previousPath:previous?.path ?? null,
          previousHash:previous?.sha256 ?? null,
          expectedCreatedAt:currentLoaded.record?.created_at ?? context.now,
          expectedStateHash:rolloverState.sha256,
          removedIds:rolloverState.value?.removedIds ?? [],
          expectedSelectedIds,
          sourceSnapshot:{
            currentMarkdown:currentLoaded.markdown,
            taskSources:rollover.taskSources,
          },
        },
      },
      completeInput:{
        ...sharedStateInput,
        operationPath,
        validatePlanTemplate:true,
        appendEvent:true,
        prepareNext:true,
        saveReview:true,
      },
    };
  }
  const completeRolloverInput = (current.id && rollover.status === 'due' && !needsRolloverWrite) ? {
    ...sharedStateInput,
    action:'complete-rollover',
    expectedPlanHash:current.sha256,
    expectedPreviousHash:previous?.sha256 ?? null,
    expectedStateHash:rolloverState.sha256,
    expectedInventoryHash:inventoryHash,
    saveReview:true,
  } : null;
  const saveReviewInput = {
    ...sharedStateInput,
    action:'save-review',
    expectedPlanHash:current.sha256,
    expectedPreviousHash:previous?.sha256 ?? null,
    expectedStateHash:reviewState.sha256,
    expectedInventoryHash:inventoryHash,
    expectedReviewHash:reviewHash,
    reviewMarkdown,
  };
  let selectionOperation = null;
  if (current.id && input.selection && ['add','remove'].includes(input.selection.action) && Array.isArray(input.selection.taskIds) && input.selection.taskIds.length) {
    const direction = input.selection.action;
    const taskIds = [...new Set(input.selection.taskIds.filter(isUuid7))];
    const tasksById = new Map([...indexed.inventory.tasks.map(t => [t.id,t]),...records.map(r => [r.id,r])]);
    const availableById = new Map([...review.selected,...review.available].map(r => [r.id,r]));
    const updatedSelected = direction === 'add'
      ? [
          ...review.selected,
          ...taskIds.filter(id => !review.selected.some(r => r.id === id)).map(id => availableById.get(id) ?? tasksById.get(id)).filter(Boolean),
        ]
      : review.selected.filter(row => !taskIds.includes(row.id));
    const updatedPlanMarkdown = draftDailyPlan(templates.templates.dailyPlan.active,{
      id:current.id,
      date:today,
      timezone:context.timezone,
      createdAt:currentLoaded.record?.created_at ?? context.now,
      now:context.now,
      displayNow,
      counts:review.counts,
      selected:updatedSelected,
      userEmail:context.profile.user.email,
      existingMarkdown:currentLoaded.markdown,
      inventory:indexed.inventory,
      records,
      projectsRoot:context.projectsRoot,
      dailyPlansRoot:context.dailyPlansRoot,
    });
    const updatedPlanSha256 = fingerprint(updatedPlanMarkdown);
    const baselinePath = path.join(context.stateRoot,'reconciliation.json');
    const baselineBeforeText = await readOrdinary(baselinePath);
    const baselineBeforeHash = fingerprint(baselineBeforeText);
    const baselineBeforeValue = baselineBeforeText === null ? {schemaVersion:1,records:{}} : JSON.parse(baselineBeforeText.replace(/^\uFEFF/,''));
    const nextRecords = structuredClone(baselineBeforeValue.records ?? {});
    const protectedFiles = [];
    for (const id of taskIds) {
      const task = tasksById.get(id);
      if (!task?.path) continue;
      const absPath = path.resolve(context.projectsRoot,task.path);
      const sha256 = sourceHashes.get(absPath) ?? fingerprint(await readOrdinary(absPath));
      if (sha256) protectedFiles.push({path:absPath,sha256});
      const existingEntry = nextRecords[id];
      const existingViews = {...(existingEntry?.views ?? {})};
      existingViews[current.path] = {selected:direction === 'add',hash:updatedPlanSha256};
      nextRecords[id] = {
        canonical:existingEntry?.canonical ?? {state:task.state ?? 'not-started'},
        views:existingViews,
      };
    }
    const operationId = uuid7();
    const operationPath = path.join(context.stateRoot,'operations',`${operationId}.json`);
    const planDescriptor = {
      date:today,
      planPath:current.path,
      planId:current.id,
      beforeMarkdown:currentLoaded.markdown,
      stateBeforeHash:rolloverState.sha256,
      stateBeforeText:rolloverState.text,
    };
    selectionOperation = {
      operationId,
      operationPath,
      planPath:current.path,
      dailyPlanMarkdown:updatedPlanMarkdown,
      checkpoint:{
        schemaVersion:2,
        operation_id:operationId,
        contextBinding:context.planningBinding,
        event:{
          id:uuid7(),
          operation_id:operationId,
          action:`selection-${direction}`,
          record_ids:taskIds,
          actor:{kind:'person',id:context.profile.user.email},
          activity_at:context.now,
          recorded_at:context.now,
          time_defaulted:false,
          original_words:typeof input.selection.originalWords === 'string' && input.selection.originalWords.trim()
            ? input.selection.originalWords.trim()
            : `Selection ${direction}`,
          before:{date:direction === 'add' ? null : today},
          after:{date:direction === 'add' ? today : null},
        },
        files:[{path:current.path,before:current.sha256,after:updatedPlanSha256}],
        protectedFiles,
        selectionState:{
          direction,
          taskIds,
          ...(direction === 'add' ? {destination:planDescriptor} : {source:planDescriptor}),
        },
        baseline:{
          beforeHash:baselineBeforeHash,
          beforeText:baselineBeforeText,
          value:{schemaVersion:1,records:nextRecords},
        },
      },
      completeInput:{
        ...sharedStateInput,
        ...(input.selection.nextPage !== undefined ? {page:input.selection.nextPage} : {}),
        operationPath,
        appendEvent:true,
        prepareNext:true,
        saveReview:true,
      },
    };
  }
  return {status:recovery.blocked || rollover.status === 'conflict' ? 'recovery-required' : current.id ? 'prepared' : 'create-plan',
    displayNow,
    pendingOperations:recovery.names,
    drafts:{
      dailyPlanMarkdown,
      dailyPlanSha256,
      reviewMarkdown,
      rolloverOperation,
      completeRolloverInput,
      saveReviewInput,
      ...(selectionOperation ? {selectionOperation} : {}),
    },
    context,current,previous,rollover,review,templates,
    maintenance:await verifiedMaintenanceStatus(input,indexed),
    recovery,inventory:indexed.inventory,inventoryStatus:indexed.status,metrics:indexed.metrics,
    enrollment:indexed.inventory.diagnostics.filter(issue => issue.code === 'invalid-id').map(issue => ({path:issue.path,
      issues:issuesByPath.get(issue.path),requiresExplicitAcceptance:true})),
    inventoryHash,reviewHash,
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
  const checkDailyPlanTemplate = input.validatePlanTemplate === true || typeof input.dailyPlanMarkdown === 'string' ||
    (input.validatePlanTemplate !== false && !prepared.templates.templates.dailyPlan.shouldOffer && Boolean(current.hasTemplateMetadata));
  if (checkDailyPlanTemplate) {
    const planValidation = typeof input.dailyPlanMarkdown === 'string'
      ? validateDailyPlan(input.dailyPlanMarkdown,prepared.templates.templates.dailyPlan.active,{selected:review.selected,counts:review.counts,userEmail:context.profile.user.email})
      : current.templateValidation;
    if (planValidation && !planValidation.valid) {
      throw new Error(`Daily plan does not match the active dailyPlan template: ${planValidation.errors.join('; ')}`);
    }
  }
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
    const refreshedRecovery = await planningOperationImpacts(input,{context,current,previous,inventory:prepared.inventory,state});
    if (refreshedRecovery.blocked || refreshedRecovery.fingerprint !== prepared.recovery.fingerprint) {
      throw new Error('Planning dependencies or checkpoint evidence changed before save; prepare again');
    }
    if (fingerprint(await readOrdinary(target.path)) !== target.sha256 || fingerprint(await readOrdinary(current.path)) !== current.sha256 ||
        (previous && fingerprint(await readOrdinary(previous.path)) !== previous.sha256)) throw new Error('Planning sources changed before save; retry');
    await rename(temporary,target.path);
  } finally { await unlink(temporary).catch(error => { if (error.code !== 'ENOENT') throw error; }); }
  const reviewSaved = (input.action === 'complete-rollover' && input.saveReview && prepared.drafts?.saveReviewInput)
    ? await savePlanningState({
        ...prepared.drafts.saveReviewInput,
        ...(typeof input.reviewMarkdown === 'string' ? {reviewMarkdown:input.reviewMarkdown} : {}),
      })
    : undefined;
  return {status:'saved',path:target.path,value,...(reviewSaved ? {reviewSaved} : {})};
}
