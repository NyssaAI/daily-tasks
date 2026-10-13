import { readFile, readdir, lstat } from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { inspectOperationImpact } from './verification.mjs';

async function operationBytes(filename) {
  const stat = await lstat(filename);
  if (!stat.isFile() || stat.isSymbolicLink()) throw new Error(`Expected an ordinary operation checkpoint: ${filename}`);
  return readFile(filename,'utf8');
}

/** Return resumable checkpoints while ignoring retained legacy completion receipts. */
export async function pendingOperationNames(stateRoot) {
  const directory = path.join(stateRoot,'operations');
  let names;
  try {
    const stat = await lstat(directory);
    if (!stat.isDirectory() || stat.isSymbolicLink()) throw new Error(`Expected an ordinary operation directory: ${directory}`);
    names = await readdir(directory);
  } catch (error) { if (error.code === 'ENOENT') return []; throw error; }
  const pending = [];
  for (const name of names.filter(candidate => candidate.endsWith('.json')).sort()) {
    const filename = path.join(directory,name);
    let operation;
    try { operation = JSON.parse((await operationBytes(filename)).replace(/^\uFEFF/,'')); }
    catch (error) {
      if (error.code === 'ENOENT') continue;
      pending.push(name);
      continue;
    }
    const historicalCompletion = operation.status === 'completed' &&
      operation.operation_id === path.basename(name,'.json') && Array.isArray(operation.files);
    if (!historicalCompletion) pending.push(name);
  }
  return pending;
}

const pathKey = filename => process.platform === 'win32' ? path.resolve(filename).toLowerCase() : path.resolve(filename);

/** Classify validated checkpoint dependencies for one prepared planning session. */
export async function planningOperationImpacts(input, {context,current,previous,inventory,records = [],state}) {
  const names = await pendingOperationNames(context.stateRoot), operations = [], diagnostics = [];
  const suspendedRecordIds = new Set(), suspendedProjectIds = new Set();
  const requiredPaths = new Set([current.path,previous?.path,state.review.path,state.rollover.path,
    path.join(context.stateRoot,'review',`${context.localDate}.json`),path.join(context.stateRoot,'planning-review.json')].filter(Boolean).map(pathKey));
  const sources = [...inventory.projects.map(record => ({...record,type:'project'})),
    ...inventory.milestones.map(record => ({...record,type:'milestone'})),
    ...inventory.tasks.map(record => ({...record,type:'task'})),...records];
  const byPath = new Map(sources.filter(record => record.path).map(record => [pathKey(path.resolve(context.projectsRoot,record.path)),record]));
  const byId = new Map(sources.map(record => [record.id,record]));
  const plannedTaskIds = new Map();
  for (const task of inventory.tasks) {
    const paths = new Set(task.planned.map(plan => pathKey(path.resolve(context.vaultRoot,plan.source))));
    for (const filename of paths) {
      if (!plannedTaskIds.has(filename)) plannedTaskIds.set(filename,[]);
      plannedTaskIds.get(filename).push(task.id);
    }
  }
  let blocked = false;
  for (const name of names) {
    const operationPath = path.join(context.stateRoot,'operations',name);
    let impact;
    try { impact = await inspectOperationImpact({...input,operationPath}); }
    catch (error) {
      blocked = true;
      operations.push({name,status:'unknown',reason:error.message});
      diagnostics.push({code:'pending-operation-unknown',operation:name,message:`Recover this checkpoint before planning: ${error.message}`});
      continue;
    }
    const affectedIds = new Set(impact.recordIds), affectedProjects = new Set();
    let overlaps = impact.statePaths.some(filename => requiredPaths.has(pathKey(filename)));
    for (const filename of impact.paths) {
      if (requiredPaths.has(pathKey(filename))) overlaps = true;
      const record = byPath.get(pathKey(filename));
      if (record) affectedIds.add(record.id);
      else {
        // A newly created/deleted source still affects its project's eligibility/order.
        const project = inventory.projects.find(candidate => {
          const directory = path.dirname(path.resolve(context.projectsRoot,candidate.path));
          const relative = path.relative(directory,filename);
          return relative !== '..' && !relative.startsWith(`..${path.sep}`) && !path.isAbsolute(relative);
        });
        if (project) affectedProjects.add(project.id);
        else {
          const relative = path.relative(context.dailyPlansRoot,filename);
          if (relative === '..' || relative.startsWith(`..${path.sep}`) || path.isAbsolute(relative)) overlaps = true;
        }
      }
      for (const id of plannedTaskIds.get(pathKey(filename)) ?? []) affectedIds.add(id);
    }
    for (const id of affectedIds) {
      const record = byId.get(id);
      if (record?.type === 'project') affectedProjects.add(id);
      if (record?.type === 'milestone') affectedProjects.add(record.projectId ?? record.project_id);
      suspendedRecordIds.add(id);
      diagnostics.push({code:'pending-operation',operation:name,recordId:id,path:record?.path,
        message:'Keep this record suspended until its pending operation is recovered'});
    }
    for (const projectId of affectedProjects) {
      suspendedProjectIds.add(projectId);
      diagnostics.push({code:'pending-project-operation',operation:name,projectId,message:'Project eligibility/order remains suspended until recovery'});
    }
    blocked ||= overlaps;
    operations.push({...impact,name,status:overlaps ? 'blocking' : affectedIds.size || affectedProjects.size ? 'scoped' : 'unrelated'});
    if (!affectedIds.size && !affectedProjects.size || overlaps) diagnostics.push({code:'pending-operation',operation:name,
      message:overlaps ? 'Current planning sources require recovery' : 'Pending operation remains outside this planning review'});
  }
  const evidence = {operations,suspendedRecordIds:[...suspendedRecordIds].sort(),suspendedProjectIds:[...suspendedProjectIds].sort(),blocked};
  return {...evidence,names,diagnostics,fingerprint:createHash('sha256').update(JSON.stringify(evidence)).digest('hex')};
}
