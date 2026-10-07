import { readFile, writeFile, readdir, lstat, realpath, mkdir, rename, unlink } from 'node:fs/promises';
import { createHash, randomUUID } from 'node:crypto';
import path from 'node:path';
import { homedir } from 'node:os';
import { parseRecord, validateRecords, checkLinks, recordIssueIsInvalid, recordMarkdownIsManaged } from '../records/records.mjs';
import { parseViewRows } from '../records/views.mjs';
import { isUuid7 } from '../identity/identity.mjs';
import { localDay, utcTimestamp } from '../time/time.mjs';
import { planningBinding } from '../profile/context.mjs';

const hash = data => createHash('sha256').update(data).digest('hex');
const slash = value => value.split(path.sep).join('/');
const relative = (root,file) => slash(path.relative(root,file));
const compareName = (a,b) => a.toLowerCase().localeCompare(b.toLowerCase(),'en') || a.localeCompare(b,'en');
const open = state => ['not-started','in-progress'].includes(state);
const inventoryRulesVersion = 3;
export function taskSummary(task) {
  return {id:task.id,projectId:task.project_id,milestoneId:task.milestone_id,path:task.path,title:task.title,state:task.state,
    owner:task.owner,assignee:task.assignee ?? null,targetDate:task.target_date ?? null,
    dependsOn:task.depends_on ?? [],blockedBy:task.blocked_by ?? [],planned:[]};
}
export function calendarDate(value) {
  if (!/^\d{4}\.\d{2}\.\d{2}$/.test(value ?? '')) return false;
  try { utcTimestamp(value.replaceAll('.','-') + 'T00:00:00Z'); return true; } catch { return false; }
}
function directoryDate(name) {
  const match = /(?:^|\D)(\d{4})[.-](\d{2})[.-](\d{2})(?:\D|$)/.exec(name);
  const value = match && `${match[1]}.${match[2]}.${match[3]}`;
  return calendarDate(value) ? value : null;
}
export function compareProjects(a,b) {
  const ad = directoryDate(a), bd = directoryDate(b);
  return ad && bd ? ad.localeCompare(bd) || compareName(a,b) : ad ? -1 : bd ? 1 : compareName(a,b);
}
async function ordinary(filename) {
  const stats = await lstat(filename);
  if (stats.isSymbolicLink()) throw new Error(`Symbolic link excluded: ${filename}`);
  return stats;
}
async function rootPath(value,name,missing = false) {
  if (!path.isAbsolute(value ?? '')) throw new TypeError(`${name} must be absolute`);
  try { if (!(await ordinary(value)).isDirectory()) throw new Error(`${name} must be a directory`); return await realpath(value); }
  catch (error) { if (missing && error.code === 'ENOENT') return path.normalize(value); throw error; }
}
function portableRoot(root,vault,home) {
  for (const [anchor,prefix] of [[vault,'./'],[home,'~/']]) {
    const rel = relative(anchor,root);
    if (rel === '' || (!rel.startsWith('../') && rel !== '..' && !path.isAbsolute(rel))) return prefix + rel;
  }
  return '@projectsRoot';
}
async function collectFiles(projectsRoot,dailyPlansRoot) {
  const files = [];
  async function visit(directory,anchor,root) {
    const entries = (await readdir(directory,{withFileTypes:true})).filter(entry => !entry.name.startsWith('.')).sort((a,b) => compareName(a.name,b.name));
    const metadata = await inventoryBatch(entries,async entry => {
      const filename = path.join(directory,entry.name);
      return {entry,filename,stats:await ordinary(filename)};
    });
    for (const {entry,filename,stats} of metadata) {
      if (stats.isDirectory()) await visit(filename,anchor,root);
      else if (stats.isFile() && /\.md$/i.test(entry.name)) files.push({anchor,path:relative(root,filename),filename,size:stats.size,mtimeMs:stats.mtimeMs,ctimeMs:stats.ctimeMs});
    }
  }
  await visit(projectsRoot,'projectsRoot',projectsRoot);
  try {
    for (const entry of (await readdir(dailyPlansRoot,{withFileTypes:true})).sort((a,b) => compareName(a.name,b.name))) {
      const match = /^(\d{4}\.\d{2}\.\d{2})-daily-plan\.md$/.exec(entry.name);
      if (!match || !calendarDate(match[1])) continue;
      const filename = path.join(dailyPlansRoot,entry.name), stats = await ordinary(filename);
      if (!stats.isFile()) throw new Error(`Daily plan must be a file: ${filename}`);
      files.push({anchor:'vaultRoot',path:entry.name,filename,date:match[1],size:stats.size,mtimeMs:stats.mtimeMs,ctimeMs:stats.ctimeMs});
    }
  } catch (error) { if (error.code !== 'ENOENT') throw error; }
  return files;
}
// Bound filesystem fan-out while preserving source order and collecting every batch.
async function inventoryBatch(items,operation) {
  const results = [];
  for (let index = 0; index < items.length; index += 16) {
    const batch = await Promise.allSettled(items.slice(index,index+16).map(operation));
    const failed = batch.find(result => result.status === 'rejected');
    if (failed) throw failed.reason;
    results.push(...batch.map(result => result.value));
  }
  return results;
}
const signatures = files => files.map(({anchor,path,size,mtimeMs,ctimeMs}) => ({anchor,path,size,mtimeMs,ctimeMs}));
async function readCache(filename) {
  try { await ordinary(filename); return await readFile(filename,'utf8'); }
  catch (error) { if (error.code === 'ENOENT') return null; throw error; }
}
function jsonOrNull(text) { try { return JSON.parse(text); } catch { return null; } }
async function cacheDirectory(vaultRoot,create) {
  let current = vaultRoot;
  for (const part of ['.temp','daily-tasks']) {
    current = path.join(current,part);
    try { if (!(await ordinary(current)).isDirectory()) throw new Error('Cache ancestor must be a directory'); }
    catch (error) { if (error.code !== 'ENOENT') throw error; if (create) await mkdir(current); }
  }
  return current;
}
async function atomicJson(filename,value) {
  try { await ordinary(filename); } catch (error) { if (error.code !== 'ENOENT') throw error; }
  const temporary = `${filename}.${randomUUID()}.tmp`;
  try { await writeFile(temporary,JSON.stringify(value,null,2) + '\n',{flag:'wx'}); await rename(temporary,filename); }
  finally { await unlink(temporary).catch(error => { if (error.code !== 'ENOENT') throw error; }); }
}

/** Rebuild/reuse script-owned derived JSON only. Canonical Markdown remains read-only. */
export async function projectInventory(input) {
  const now = utcTimestamp(input.now ?? new Date().toISOString());
  const today = localDay(now,input.timezone);
  const ttlSeconds = input.ttlSeconds ?? input.profile?.projectIndex?.ttlSeconds ?? 14400;
  if (!Number.isSafeInteger(ttlSeconds) || ttlSeconds < 0) throw new TypeError('ttlSeconds must be a nonnegative integer');
  const [vaultRoot,projectsRoot,dailyPlansRoot] = await Promise.all([
    rootPath(input.vaultRoot,'vaultRoot'),rootPath(input.projectsRoot,'projectsRoot'),rootPath(input.dailyPlansRoot,'dailyPlansRoot',true)
  ]);
  const dailyRelative = relative(vaultRoot,dailyPlansRoot);
  if (dailyRelative === '..' || dailyRelative.startsWith('../') || path.isAbsolute(dailyRelative)) throw new Error('dailyPlansRoot must be beneath vaultRoot');
  const scope = {projectsRoot:portableRoot(projectsRoot,vaultRoot,input.homeRoot ?? homedir()),dailyPlansRoot:'./' + dailyRelative};
  const sessionBinding = planningBinding(input);
  const directory = await cacheDirectory(vaultRoot,false);
  const filename = path.join(directory,'project-index.json'), freshnessPath = path.join(directory,'project-index-freshness.json');
  const files = await collectFiles(projectsRoot,dailyPlansRoot);
  for (const file of files) if (file.anchor === 'vaultRoot') file.path = relative(vaultRoot,file.filename);
  const metadata = signatures(files), binding = planningBinding({vaultRoot,projectsRoot,dailyPlansRoot});
  const [cachedText,freshnessText] = await Promise.all([readCache(filename),readCache(freshnessPath)]);
  const cache = jsonOrNull(cachedText), freshness = jsonOrNull(freshnessText);
  const age = cache?.generatedAt ? Date.parse(now) - Date.parse(cache.generatedAt) : NaN;
  const compatible = cache?.schemaVersion === 1 && ['projects','milestones','tasks','blockers','sources','diagnostics'].every(key => Array.isArray(cache[key])) &&
    JSON.stringify(cache.scope) === JSON.stringify(scope) && freshness?.binding === binding &&
    freshness.inventoryHash === hash(cachedText ?? '') && freshness.fromDate === today && freshness.rulesVersion === inventoryRulesVersion;
  if (!input.forceRefresh && compatible && age >= 0 && age < ttlSeconds * 1000 &&
      JSON.stringify(freshness.files) === JSON.stringify(metadata)) return {status:'reused',path:filename,planningBinding:sessionBinding,inventory:cache,metrics:{sourceReads:0,metadataFiles:files.length}};
  const records = [], sources = [], plans = [];
  let sourceReads = 0;
  // History supplies carry-forward separately; only active plans contribute allocations.
  const loaded = await inventoryBatch(files.filter(file => !file.date || file.date >= today),async file => {
    const text = await readFile(file.filename,'utf8');
    const after = await ordinary(file.filename);
    if (after.size !== file.size || after.mtimeMs !== file.mtimeMs || after.ctimeMs !== file.ctimeMs) throw new Error('Source changed during inventory refresh; retry');
    return {file,text};
  });
  sourceReads = loaded.length;
  for (const {file,text} of loaded) {
    sources.push({anchor:file.anchor,path:file.path,sha256:hash(text)});
    if (file.date) plans.push({...file,rows:parseViewRows(text).filter(row => row.mark !== undefined)});
    else if (recordMarkdownIsManaged(text,file.path)) {
      records.push(parseRecord(text,file.path));
    }
  }
  const diagnostics = [...validateRecords(records),...checkLinks(records.map(record => ({...record,path:path.join(projectsRoot,record.path)})))].map(d => ({...d,path:path.isAbsolute(d.path ?? '') ? relative(projectsRoot,d.path) : d.path}));
  const canonical = new Map(records.map(r => [r.id,r]));
  for (const record of records) for (const projection of record.projections) {
    const target = canonical.get(projection.id);
    if (!target) continue;
    const done = target.type === 'blocker' ? 'resolved' : 'completed';
    if ((projection.state && projection.state !== target.state) || projection.checked !== (target.state === done)) {
      diagnostics.push({code:'view-state-difference',recordId:target.id,path:record.path,message:'Reconcile this editable view against its baseline before planning affected work'});
    }
  }
  const invalidIds = new Set(diagnostics.filter(recordIssueIsInvalid).map(d => d.recordId));
  // Preserve invalid ancestors as explicit barriers after filtering their summaries.
  const referencedProjects = new Map(), childProjects = new Map();
  for (const record of records) {
    if (record.type === 'project') for (const ref of record.refs) {
      if (!referencedProjects.has(ref.id)) referencedProjects.set(ref.id,new Set());
      referencedProjects.get(ref.id).add(record.id);
    }
    if (record.milestone_id) {
      if (!childProjects.has(record.milestone_id)) childProjects.set(record.milestone_id,new Set());
      childProjects.get(record.milestone_id).add(record.project_id);
    }
  }
  for (const record of records.filter(r => invalidIds.has(r.id))) {
    if (!['project','milestone'].includes(record.type) && !childProjects.has(record.id) &&
        !(record.project_id && !record.milestone_id && referencedProjects.has(record.id))) continue;
    const affectedProjects = new Set([...(referencedProjects.get(record.id) ?? []),...(childProjects.get(record.id) ?? [])]);
    affectedProjects.add(record.type === 'project' ? record.id : record.project_id);
    for (const projectId of affectedProjects) if (isUuid7(projectId)) {
      diagnostics.push({code:'invalid-planning-scope',recordId:record.id,projectId,path:record.path,
        message:'Invalid ancestor facts prevent establishing this project\'s eligible milestone; preserve selections and resolve the validation errors first'});
    }
  }
  const uncertainIndexIds = new Set(diagnostics.filter(d => ['missing-reference','duplicate-reference'].includes(d.code)).map(d => d.recordId));
  for (const project of records.filter(r => r.type === 'project' && uncertainIndexIds.has(r.id))) {
    diagnostics.push({code:'invalid-planning-scope',recordId:project.id,projectId:project.id,path:project.path,
      message:'Unresolved project-index identities prevent establishing milestone order; preserve selections and resolve the referenced records first'});
  }
  const valid = records.filter(r => !invalidIds.has(r.id));
  const projectRecords = valid.filter(r => r.type === 'project').sort((a,b) => compareProjects(a.path.split('/')[0],b.path.split('/')[0]));
  const inventory = {schemaVersion:1,generatedAt:now,scope,projects:[],milestones:[],tasks:[],blockers:[],sources,diagnostics};
  const summary = r => ({id:r.id,path:r.path,title:r.title,state:r.state});
  const milestonesByProject = new Map(), tasksByMilestone = new Map();
  for (const record of valid) {
    const group = record.type === 'milestone' ? milestonesByProject : record.type === 'task' && open(record.state) ? tasksByMilestone : null;
    if (!group) continue;
    const key = record.type === 'milestone' ? record.project_id : record.milestone_id;
    if (!group.has(key)) group.set(key,[]);
    group.get(key).push(record);
  }
  const order = (sequence,items) => {
    for (const item of items) if (!sequence.has(item.id)) diagnostics.push({code:'missing-order',recordId:item.id,path:item.path,message:'Project index must reference this record to establish order'});
    return items.sort((a,b) => {
      return (sequence.get(a.id) ?? Infinity) - (sequence.get(b.id) ?? Infinity) || compareName(a.path,b.path);
    });
  };
  for (const project of projectRecords) {
    const sequence = new Map();
    project.refs.forEach((ref,index) => { if (!sequence.has(ref.id)) sequence.set(ref.id,index); });
    inventory.projects.push({...summary(project),owner:project.owner});
    for (const milestone of order(sequence,milestonesByProject.get(project.id) ?? [])) {
      inventory.milestones.push({...summary(milestone),projectId:project.id});
      for (const task of order(sequence,(tasksByMilestone.get(milestone.id) ?? []).filter(r => r.project_id === project.id))) {
        inventory.tasks.push(taskSummary(task));
      }
    }
  }
  for (const blocker of valid.filter(r => r.type === 'blocker')) inventory.blockers.push({...summary(blocker),owner:blocker.owner,blocks:blocker.blocks});
  const byId = new Map(inventory.tasks.map(t => [t.id,t]));
  const allocations = new Map();
  for (const plan of plans) {
    const seen = new Set();
    for (const row of plan.rows) {
      const target = canonical.get(row.id);
      if (target?.type === 'task' && ((row.state && row.state !== target.state) || row.checked !== (target.state === 'completed'))) {
        diagnostics.push({code:'view-state-difference',recordId:row.id,path:plan.path,message:'Reconcile this editable plan against its baseline before planning affected work'});
      }
      if (row.checked || row.cancelled) continue;
      if (!isUuid7(row.id)) { diagnostics.push({code:'selection-identity',path:plan.path,message:'Active plan selection requires a task UUID'}); continue; }
      if (seen.has(row.id)) { diagnostics.push({code:'duplicate-selection',recordId:row.id,path:plan.path,message:'Task appears more than once in the same plan'}); continue; }
      seen.add(row.id);
      if (!byId.has(row.id)) {
        if (!records.some(r => r.id === row.id && r.type === 'task' && !open(r.state))) diagnostics.push({code:'selection-identity',recordId:row.id,path:plan.path,message:'Active plan points to a missing or invalid task'});
        continue;
      }
      if (!allocations.has(row.id)) allocations.set(row.id,[]);
      allocations.get(row.id).push({date:plan.date,source:plan.path});
    }
  }
  for (const [id,entries] of allocations) {
    if (entries.length > 1) diagnostics.push({code:'multiple-planning-dates',recordId:id,message:'Resolve conflicting active planning dates',sources:entries});
    else byId.get(id).planned = entries;
  }
  // A membership/metadata race cannot produce a successful new freshness timestamp.
  const afterFiles = await collectFiles(projectsRoot,dailyPlansRoot);
  for (const file of afterFiles) if (file.anchor === 'vaultRoot') file.path = relative(vaultRoot,file.filename);
  if (JSON.stringify(metadata) !== JSON.stringify(signatures(afterFiles))) throw new Error('Sources changed during inventory refresh; retry');
  if (!input.dryRun) {
    await cacheDirectory(vaultRoot,true);
    const serialized = JSON.stringify(inventory,null,2) + '\n';
    await atomicJson(freshnessPath,{schemaVersion:1,rulesVersion:inventoryRulesVersion,binding,fromDate:today,files:metadata,inventoryHash:hash(serialized)});
    // Commit the visible inventory last. A failed sidecar write preserves generatedAt.
    await atomicJson(filename,inventory);
  }
  return {status:input.dryRun ? 'preview' : 'rebuilt',path:filename,planningBinding:sessionBinding,inventory,metrics:{sourceReads,metadataFiles:files.length}};
}

export async function invalidateInventory(input) {
  const vaultRoot = await rootPath(input.vaultRoot,'vaultRoot');
  const directory = await cacheDirectory(vaultRoot,false);
  const filename = path.join(directory,'project-index-freshness.json');
  const exists = await readCache(filename);
  if (exists && !input.dryRun) await unlink(filename);
  return {invalidated:!!exists,dryRun:!!input.dryRun};
}
