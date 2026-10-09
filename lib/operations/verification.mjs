import { readFile, lstat, mkdir, writeFile, rename, unlink, readdir } from 'node:fs/promises';
import { createHash, randomUUID } from 'node:crypto';
import path from 'node:path';
import { isDeepStrictEqual } from 'node:util';
import { resolveContext } from '../profile/context.mjs';
import { isUuid7 } from '../identity/identity.mjs';
import { queryDecisions } from '../log/decision-log.mjs';
import { parseRecord } from '../records/records.mjs';
import { parseChecklist, planRollover } from '../planning/planning.mjs';
import { projectInventory, calendarDate } from '../inventory/inventory.mjs';
import { utcTimestamp } from '../time/time.mjs';
import { navigationLinks } from '../records/navigation.mjs';
import { recordDirectoryIsHoldingArea } from '../records/records.mjs';

const hash = bytes => bytes === null ? null : createHash('sha256').update(bytes).digest('hex');
const validHash = value => value === null || /^[a-f0-9]{64}$/.test(value ?? '');
const within = (root, target) => { const relative = path.relative(root,target); return relative === '' || (!path.isAbsolute(relative) && relative !== '..' && !relative.startsWith(`..${path.sep}`)); };

async function ordinary(filename) {
  const directories = [];
  for (let current = path.dirname(filename); ; current = path.dirname(current)) {
    directories.push(current);
    if (current === path.dirname(current)) break;
  }
  for (const directory of directories.reverse()) {
    try { const stat = await lstat(directory); if (!stat.isDirectory() || stat.isSymbolicLink()) throw new Error(`Unsafe directory: ${directory}`); }
    catch (error) { if (error.code !== 'ENOENT') throw error; }
  }
  try {
    const stat = await lstat(filename);
    if (!stat.isFile() || stat.isSymbolicLink()) throw new Error(`Unsafe file: ${filename}`);
    return await readFile(filename);
  } catch (error) { if (error.code === 'ENOENT') return null; throw error; }
}

function effectPath(context, filename) {
  if (typeof filename !== 'string' || !path.isAbsolute(filename) ||
      ![context.projectsRoot,context.dailyPlansRoot].some(root => within(root,filename)) ||
      [context.stateRoot,context.configRoot].some(root => within(root,filename)) ||
      [context.projectsRoot,context.dailyPlansRoot].filter(root => within(root,filename)).some(root => path.relative(root,filename).split(path.sep).some(part => part.startsWith('.')))) throw new Error('Effect path must be an ordinary project or daily-plan source outside log/config/state');
  return path.normalize(filename);
}

async function load(input) {
  if (['actual','verified','operation','checkpoint'].some(key => Object.hasOwn(input,key))) throw new Error('Caller-supplied actual values or checkpoints are not verification evidence');
  const context = await resolveContext(input);
  if (!context.configured) throw new Error('Configured context required');
  const filename = input.operationPath;
  if (!path.isAbsolute(filename ?? '') || path.dirname(filename) !== path.join(context.stateRoot,'operations') || !isUuid7(path.basename(filename,'.json')) || path.extname(filename) !== '.json') throw new Error('Operation path must be stateRoot/operations/UUID.json');
  const bytes = await ordinary(filename);
  if (bytes === null) throw new Error('Operation checkpoint missing');
  const operation = JSON.parse(bytes.toString('utf8'));
  if (operation.schemaVersion !== 2 || operation.operation_id !== path.basename(filename,'.json') || operation.contextBinding !== context.planningBinding || !Array.isArray(operation.files) || !operation.files.length || operation.event?.operation_id !== operation.operation_id) throw new Error('Invalid bound schemaV2 operation checkpoint');
  const seen = new Set();
  for (const file of operation.files) {
    file.path = effectPath(context,file.path);
    if (seen.has(file.path) || !validHash(file.before) || !validHash(file.after)) throw new Error('Effects require unique paths and explicit before/after hashes');
    seen.add(file.path);
  }
  for (const file of operation.protectedFiles ?? []) {
    effectPath(context,file.path);
    if (!validHash(file.sha256)) throw new Error('Protection hash required');
  }
  return {context,operation,filename,checkpointHash:hash(bytes)};
}

async function verifyLoaded(loaded) {
  const {context,operation} = loaded;
  const pending = [], conflicts = [];
  for (const file of operation.files) {
    const actual = hash(await ordinary(file.path));
    if (actual === file.after) continue;
    (actual === file.before ? pending : conflicts).push({path:file.path,actual,before:file.before,after:file.after});
  }
  for (const file of operation.protectedFiles ?? []) if (hash(await ordinary(file.path)) !== file.sha256) conflicts.push({path:file.path,reason:'protected-source-changed'});
  let event = null;
  for (let offset = 0; offset !== null;) {
    const page = await queryDecisions({projectsRoot:context.projectsRoot,dryRun:true,limit:1000,offset});
    for (const candidate of page.entries) if (candidate.operation_id === operation.operation_id) event = candidate;
    offset = page.nextOffset;
  }
  if (event && !isDeepStrictEqual(event,operation.event)) conflicts.push({reason:'event-conflict'});
  if (!event) pending.push({reason:'event-missing'});
  return {status:conflicts.length ? 'conflict' : pending.length ? 'pending' : 'verified',operationId:operation.operation_id,pending,conflicts,verifiedPaths:operation.files.map(file => file.path)};
}

/** Verify only declared effects; this does not claim unobserved files are unchanged. */
export async function verifyOperation(input) { return verifyLoaded(await load(input)); }

async function atomic(filename, value, expectedHash) {
  await ordinary(filename);
  await mkdir(path.dirname(filename),{recursive:true});
  await ordinary(filename);
  const temporary = `${filename}.${randomUUID()}.tmp`;
  try {
    await writeFile(temporary,JSON.stringify(value,null,2)+'\n',{flag:'wx'});
    if (hash(await ordinary(filename)) !== expectedHash) throw new Error('State changed before completion');
    await rename(temporary,filename);
  } finally { await unlink(temporary).catch(error => { if (error.code !== 'ENOENT') throw error; }); }
}

async function validateBaseline(loaded) {
  const {context,operation} = loaded, baseline = operation.baseline;
  if (!baseline) return;
  const plain = value => value && typeof value === 'object' && !Array.isArray(value);
  const shape = value => plain(value) && value.schemaVersion === 1 && plain(value.records) && Object.keys(value).every(key => ['schemaVersion','records'].includes(key));
  if (!validHash(baseline.beforeHash) || !shape(baseline.value)) throw new Error('Baseline requires schemaVersion1 records map and beforeHash');
  const beforeText = baseline.beforeText ?? null;
  if (hash(beforeText === null ? null : Buffer.from(beforeText)) !== baseline.beforeHash) throw new Error('Baseline beforeText must prove the beforeHash');
  const before = beforeText === null ? {schemaVersion:1,records:{}} : JSON.parse(beforeText);
  if (!shape(before)) throw new Error('Unsupported baseline before shape');
  const affected = new Set(operation.files.map(file => file.path));
  const indexed = await projectInventory({...context,dryRun:true,forceRefresh:true});
  const records = new Map();
  for (const source of indexed.inventory.sources.filter(source => source.anchor === 'projectsRoot')) {
    const filename = effectPath(context,path.resolve(context.projectsRoot,source.path));
    const bytes = await ordinary(filename);
    if (hash(bytes) !== source.sha256) throw new Error('Canonical source changed during baseline verification');
    const record = parseRecord(bytes.toString(),filename);
    if (record.id) { if (records.has(record.id)) throw new Error('Duplicate canonical identity'); records.set(record.id,record); }
  }
  for (const id of Object.keys(before.records)) if (!Object.hasOwn(baseline.value.records,id) && (id !== loaded.retiringId || records.has(id))) throw new Error('Baseline cannot retire records through generic completion');
  for (const [id,entry] of Object.entries(baseline.value.records)) {
    const old = before.records[id];
    if (isDeepStrictEqual(entry,old)) continue;
    if (!isUuid7(id) || !plain(entry) || !plain(entry.canonical) || !plain(entry.views) || Object.keys(entry).some(key => !['canonical','views'].includes(key))) throw new Error('Unsupported baseline record shape');
    const record = records.get(id);
    if (!record) throw new Error('Baseline canonical record missing');
    if (!isDeepStrictEqual(entry.canonical,old?.canonical) && !affected.has(record.path)) throw new Error('Baseline changed unrelated canonical fields');
    for (const [field,value] of Object.entries(entry.canonical)) if (!Object.hasOwn(record,field) || !isDeepStrictEqual(record[field],value)) throw new Error(`Baseline canonical field does not match actual ${field}`);
    for (const filename of new Set([...Object.keys(entry.views),...Object.keys(old?.views ?? {})])) {
      effectPath(context,filename);
      const view = entry.views[filename];
      if (isDeepStrictEqual(view,old?.views?.[filename])) continue;
      if (!affected.has(filename)) throw new Error('Baseline changed unrelated view');
      const bytes = await ordinary(filename);
      const rows = bytes === null ? [] : parseChecklist(bytes.toString());
      const matches = rows.filter(row => row.id === id && row.selected !== false);
      if (!view) { if (matches.length) throw new Error('Baseline dropped live view'); continue; }
      if (!plain(view) || Object.keys(view).some(key => !['hash','selected','checked','state'].includes(key)) || !/^[a-f0-9]{64}$/.test(view.hash ?? '') || hash(bytes) !== view.hash || matches.length > 1) throw new Error('Baseline view hash or shape does not match actual');
      if (Object.hasOwn(view,'selected') && view.selected !== (matches.length === 1)) throw new Error('Baseline selected field does not match actual');
      for (const field of ['checked','state']) if (Object.hasOwn(view,field) && (!matches.length || !isDeepStrictEqual(view[field],matches[0][field]))) throw new Error(`Baseline view ${field} does not match actual`);
    }
  }
}

async function finish(input, loaded, rollover) {
  const result = await verifyLoaded(loaded);
  if (result.status !== 'verified') return result;
  const {context,operation,filename} = loaded;
  const baseline = operation.baseline;
  const baselinePath = path.join(context.stateRoot,'reconciliation.json');
  await validateBaseline(loaded);
  if (baseline) {
    const actual = await ordinary(baselinePath);
    if (hash(actual) !== baseline.beforeHash && !isDeepStrictEqual(actual === null ? null : JSON.parse(actual),baseline.value)) throw new Error('Baseline changed');
  }
  if (input.dryRun) return {...result,status:'preview'};
  if (hash(await ordinary(filename)) !== loaded.checkpointHash) throw new Error('Checkpoint changed');
  // Repeat reads immediately before owned state writes; retain checkpoint on every failure.
  const repeated = await verifyLoaded(loaded);
  if (repeated.status !== 'verified') return repeated;
  if (rollover) await atomic(rollover.path,rollover.value,rollover.beforeHash);
  if (baseline) {
    const actual = await ordinary(baselinePath);
    if (!isDeepStrictEqual(actual === null ? null : JSON.parse(actual),baseline.value)) await atomic(baselinePath,baseline.value,baseline.beforeHash);
  }
  if (hash(await ordinary(filename)) !== loaded.checkpointHash) throw new Error('Checkpoint changed before clear');
  await unlink(filename);
  return {...result,status:'completed'};
}

export async function completeOperation(input) {
  const loaded = await load(input);
  if (loaded.operation.rollover || loaded.operation.migration) throw new Error('Specialized completion required');
  return finish(input,loaded);
}

export async function completeChangedRollover(input) {
  const loaded = await load(input);
  const {context,operation} = loaded, intent = operation.rollover;
  if (!intent || !calendarDate(intent.date) || intent.date > context.localDate || !isUuid7(intent.planId) || !intent.sourceSnapshot || !(intent.sourceSnapshot.currentMarkdown === null || typeof intent.sourceSnapshot.currentMarkdown === 'string') || !Array.isArray(intent.sourceSnapshot.taskSources)) throw new Error('Rollover requires bound original plan and task source evidence');
  const currentPath = path.join(context.dailyPlansRoot,`${intent.date}-daily-plan.md`);
  const effect = operation.files.find(file => file.path === currentPath);
  if (!effect || hash(intent.sourceSnapshot.currentMarkdown === null ? null : Buffer.from(intent.sourceSnapshot.currentMarkdown)) !== effect.before) throw new Error('Original plan snapshot does not match checkpoint before hash');
  for (const source of intent.sourceSnapshot.taskSources) {
    effectPath(context,source.path);
    if (!validHash(source.sha256) || hash(await ordinary(source.path)) !== source.sha256) throw new Error('Rollover task source changed');
  }
  const previousNames = (await readdir(context.dailyPlansRoot)).filter(name => /^\d{4}\.\d{2}\.\d{2}-daily-plan\.md$/.test(name) && name.slice(0,10) < intent.date).sort();
  const actualPreviousPath = previousNames.length ? path.join(context.dailyPlansRoot,previousNames.at(-1)) : null;
  if ((intent.previousPath ?? null) !== actualPreviousPath) throw new Error('Previous plan must be the actual nearest earlier plan');
  const previousBytes = actualPreviousPath === null ? null : await ordinary(effectPath(context,intent.previousPath));
  if (hash(previousBytes) !== intent.previousHash) throw new Error('Previous plan changed');
  const previous = previousBytes === null ? null : parseRecord(previousBytes.toString(),intent.previousPath);
  if ((previous?.id ?? null) !== intent.previousPlanId || (previous && (previous.type !== 'daily-plan' || !isUuid7(previous.id) || previous.parse_errors.length))) throw new Error('Previous plan identity or type changed');
  const currentBytes = await ordinary(currentPath);
  if (currentBytes === null) throw new Error('Current plan missing');
  const current = parseRecord(currentBytes.toString(),currentPath), original = intent.sourceSnapshot.currentMarkdown === null ? null : parseRecord(intent.sourceSnapshot.currentMarkdown,currentPath);
  utcTimestamp(intent.expectedCreatedAt);
  if (current.type !== 'daily-plan' || current.parse_errors.length || current.id !== intent.planId || current.created_at !== intent.expectedCreatedAt ||
      (original && (original.id !== intent.planId || original.created_at !== current.created_at))) throw new Error('Rollover plan identity or creation time changed');
  const indexed = await projectInventory({...context,dryRun:true,forceRefresh:true});
  const records = [];
  for (const source of intent.sourceSnapshot.taskSources) records.push(parseRecord((await ordinary(source.path)).toString(),source.path));
  const removed = new Set(intent.removedIds ?? []);
  const expected = planRollover({today:intent.date,planId:intent.planId,userEmail:context.profile.user.email,currentRows:parseChecklist(intent.sourceSnapshot.currentMarkdown ?? '').filter(row => !removed.has(row.id)),previousRows:parseChecklist(previousBytes?.toString() ?? ''),previousDate:actualPreviousPath === null ? undefined : path.basename(intent.previousPath).slice(0,10),removedIds:intent.removedIds,records,inventory:indexed.inventory});
  const actualIds = parseChecklist(currentBytes.toString()).filter(row => row.selected !== false).map(row => row.id);
  const expectedIds = expected.selected.filter(row => row.selected !== false).map(row => row.id);
  const sortedActualIds = [...actualIds].sort();
  if (expected.unresolved.length || new Set(actualIds).size !== actualIds.length || !isDeepStrictEqual(sortedActualIds,[...expectedIds].sort()) || !isDeepStrictEqual(sortedActualIds,[...(intent.expectedSelectedIds ?? [])].sort())) throw new Error('Rollover membership cannot be verified');
  const target = path.join(context.stateRoot,'rollover',`${intent.date}.json`), bytes = await ordinary(target);
  const existing = bytes === null ? null : JSON.parse(bytes);
  if (existing?.operationId !== operation.operation_id && (intent.expectedStateHash ?? null) !== hash(bytes)) throw new Error('Rollover state changed since checkpoint');
  if (existing && (existing.schemaVersion !== 1 || existing.planId !== intent.planId || existing.date !== intent.date || !isDeepStrictEqual(existing.removedIds ?? [],intent.removedIds ?? []))) throw new Error('Rollover state conflicts');
  if (existing?.operationId === operation.operation_id) utcTimestamp(existing.completedAt);
  const value = existing?.operationId === operation.operation_id ? existing : {schemaVersion:1,date:intent.date,planId:intent.planId,operationId:operation.operation_id,completedAt:context.now,removedIds:intent.removedIds ?? []};
  if (existing && existing.operationId !== operation.operation_id && (existing.operationId || existing.completedAt || existing.planId !== intent.planId || existing.date !== intent.date || !isDeepStrictEqual(existing.removedIds ?? [],intent.removedIds ?? []))) throw new Error('Rollover state conflicts');
  operation.protectedFiles = [...(operation.protectedFiles ?? []),...(actualPreviousPath === null ? [] : [{path:intent.previousPath,sha256:intent.previousHash}]),...intent.sourceSnapshot.taskSources];
  return finish(input,loaded,{path:target,value,beforeHash:hash(bytes)});
}

async function inspectMigration(loaded, retired = false) {
  const {context,operation} = loaded, intent = operation.migration;
  if (!intent) throw new Error('Migration retirement intent required');
  const sourcePath = effectPath(context,intent.retiringPath), destinationPath = effectPath(context,intent.destinationPath);
  let sourceBytes = await ordinary(sourcePath);
  const destinationBytes = await ordinary(destinationPath);
  const issues = [];
  if (retired) {
    const snapshot = operation.sourceSnapshot?.retiringMarkdown ?? intent.sourceSnapshot?.retiringMarkdown;
    const effect = operation.files.find(file => file.path === sourcePath);
    if (sourceBytes !== null || typeof snapshot !== 'string' || !effect || effect.before !== intent.sourceHash || effect.after !== null || hash(Buffer.from(snapshot)) !== intent.sourceHash || !operation.files.some(file => file.path === destinationPath && file.after === hash(destinationBytes))) return {allowed:false,issues:['retirement-snapshot-or-effects-not-proven']};
    sourceBytes = Buffer.from(snapshot);
  }
  if (sourcePath === destinationPath || sourceBytes === null || hash(sourceBytes) !== intent.sourceHash || destinationBytes === null) return {allowed:false,issues:['source-or-destination-evidence-missing']};
  const sourceMarkdown = sourceBytes.toString(), destinationMarkdown = destinationBytes.toString();
  const source = parseRecord(sourceMarkdown,sourcePath), destination = parseRecord(destinationMarkdown,destinationPath);
  if (source.parse_errors.length || destination.parse_errors.length || !isUuid7(source.id) || !isUuid7(destination.id) || !['task','milestone'].includes(destination.type)) issues.push({reason:'invalid-migration-record'});
  for (const criterion of source.criteria) if (!destination.criteria.some(item => isDeepStrictEqual(item,criterion))) issues.push({reason:'criterion-not-preserved',id:criterion.id});
  if (!Array.isArray(intent.expectedCriteria) || !isDeepStrictEqual(source.criteria,intent.expectedCriteria)) issues.push({reason:'criterion-intent-does-not-match-source'});
  if (new Set(destination.criteria.map(item => item.id)).size !== destination.criteria.length || destination.criteria.some(item => !isUuid7(item.id))) issues.push({reason:'invalid-destination-criteria'});
  if (!source.criteria.length) issues.push({reason:'no-verifiable-source-criteria'});
  for (const [field,value] of Object.entries(intent.preservedFields ?? {})) if (!isDeepStrictEqual(source[field],value) || !isDeepStrictEqual(destination[field],value)) issues.push({reason:'field-not-preserved',field});
  // Arbitrary narrative/history cannot be proved from selected fields alone.
  for (const line of sourceMarkdown.split(/\r?\n/).filter(line => line.trim() && !/^---$|^[a-z][a-z_-]*:|^#|^\s*- \[[ xX]\]|<!--\s*id:/.test(line))) if (!destinationMarkdown.includes(line)) issues.push({reason:'source-content-not-preserved',line});
  async function scan(directory) {
    let entries;
    try { entries = await readdir(directory,{withFileTypes:true}); }
    catch (error) { if (error.code === 'ENOENT' && directory === context.dailyPlansRoot) return; throw error; }
    for (const entry of entries) {
      if (entry.name.startsWith('.')) continue;
      const filename = path.join(directory,entry.name);
      if (entry.isSymbolicLink()) { issues.push({reason:'unscannable-link',path:filename}); continue; }
      if (entry.isDirectory()) { if (!recordDirectoryIsHoldingArea(path.relative(context.projectsRoot,filename))) await scan(filename); }
      else if (entry.isFile() && /\.md$/i.test(entry.name) && filename !== sourcePath) {
        const markdown = (await ordinary(filename)).toString();
        if (filename !== destinationPath) {
          const record = parseRecord(markdown,filename);
          if (record.refs.some(reference => reference.id === source.id)) issues.push({reason:'live-incoming-reference',path:filename,id:source.id});
          if (record.id === destination.id) issues.push({reason:'destination-identity-collision',path:filename});
          for (const criterion of record.criteria) if (destination.criteria.some(item => item.id === criterion.id)) issues.push({reason:'criterion-identity-collision',path:filename,id:criterion.id});
        }
        for (const link of navigationLinks(markdown)) {
          let target = link.target.split('#')[0];
          try { target = decodeURIComponent(target); } catch { issues.push({reason:'unreadable-link',path:filename}); continue; }
          if (/^[a-z]+:/i.test(target)) continue;
          const resolved = path.resolve(path.dirname(filename),target);
          if (resolved === sourcePath || `${resolved}.md` === sourcePath ||
              (link.wiki && !target.includes('/') && !target.includes('\\') && path.basename(target,'.md') === path.basename(sourcePath,'.md'))) issues.push({reason:'live-incoming-link',path:filename,target});
        }
      }
    }
  }
  for (const root of new Set([context.projectsRoot,context.dailyPlansRoot])) await scan(root);
  return {allowed:issues.length === 0,issues,retiringPath:sourcePath,destinationPath,retiringId:source.id,retiringType:source.type,destinationId:destination.id};
}

export async function inspectMigrationRetirement(input) { return inspectMigration(await load(input)); }

/** Called under the log lock: inspect source evidence without querying the log. */
export async function assertMigrationDecision(input, entry) {
  const loaded = await load(input);
  if (path.relative(path.resolve(input.projectsRoot),loaded.context.projectsRoot) !== '') throw new Error('Migration projectsRoot differs from resolved context');
  if (!isDeepStrictEqual(entry,loaded.operation.event)) throw new Error('Migration event differs from bound checkpoint event');
  const inspection = await inspectMigration(loaded,true);
  if (!inspection.allowed) throw new Error(`Migration retirement not verified: ${JSON.stringify(inspection.issues)}`);
  for (const file of loaded.operation.files) if (hash(await ordinary(file.path)) !== file.after) throw new Error('Migration effect not persisted');
  for (const file of loaded.operation.protectedFiles ?? []) if (hash(await ordinary(file.path)) !== file.sha256) throw new Error('Migration protected source changed');
  if (hash(await ordinary(loaded.filename)) !== loaded.checkpointHash) throw new Error('Migration checkpoint changed before log append');
}

/** Verify post-retirement effects; cannot attest whether inspection preceded deletion. */
export async function completeMigration(input) {
  const loaded = await load(input);
  const inspection = await inspectMigration(loaded,true);
  if (!inspection.allowed) return {status:'conflict',operationId:loaded.operation.operation_id,conflicts:inspection.issues,pending:[]};
  if (inspection.retiringType === 'dod' && inspection.retiringId !== inspection.destinationId) loaded.retiringId = inspection.retiringId;
  return finish(input,loaded);
}
