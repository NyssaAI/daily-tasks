import { lstat, mkdir, readdir, readFile, open, rename, unlink, rmdir } from 'node:fs/promises';
import path from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';
import { isUuid7, uuid7 } from '../identity/identity.mjs';
import { utcTimestamp } from '../time/time.mjs';

const filenamePattern = /^\d{4}\.\d{2}\.\d{2}-decisions(?:-\d{6})?\.json$/;
const fields = new Set(['id','operation_id','action','record_ids','actor','activity_at','recorded_at','time_defaulted','original_words','before','after','corrects']);
function fail(code, message) { throw Object.assign(new Error(message), { code }); }
function plain(value) { return value !== null && typeof value === 'object' && !Array.isArray(value) && Object.getPrototypeOf(value) === Object.prototype; }
function jsonValue(value) {
  if (value === null || typeof value === 'string' || typeof value === 'boolean') return true;
  if (typeof value === 'number') return Number.isFinite(value);
  if (Array.isArray(value)) return value.every(jsonValue);
  return plain(value) && Object.values(value).every(jsonValue);
}
function utc(value) {
  try { utcTimestamp(value); return true; } catch { return false; }
}
function validateEntry(entry) {
  if (!plain(entry) || Object.keys(entry).some(key => !fields.has(key))) fail('INVALID_ENTRY','Invalid decision entry or unknown field');
  if (!isUuid7(entry.id) || !isUuid7(entry.operation_id)) fail('INVALID_ENTRY','Decision id and operation_id must be UUIDv7');
  if (typeof entry.action !== 'string' || !entry.action.trim()) fail('INVALID_ENTRY','Decision action is required');
  if (!Array.isArray(entry.record_ids) || !entry.record_ids.every(isUuid7) || new Set(entry.record_ids).size !== entry.record_ids.length) fail('INVALID_ENTRY','record_ids must be distinct UUIDv7 values');
  if (!plain(entry.actor) || Object.keys(entry.actor).some(key => !['kind','id'].includes(key)) || !['person','agent'].includes(entry.actor.kind) || typeof entry.actor.id !== 'string' || !entry.actor.id.trim()) fail('INVALID_ENTRY','Actor kind and identity are required');
  if (entry.actor.kind === 'person' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(entry.actor.id)) fail('INVALID_ENTRY','Person actor identity must be an email address');
  if (!utc(entry.activity_at) || !utc(entry.recorded_at)) fail('INVALID_ENTRY','Activity and recorded timestamps must be valid GMT ISO timestamps');
  if (typeof entry.time_defaulted !== 'boolean') fail('INVALID_ENTRY','time_defaulted must be boolean');
  if ('original_words' in entry && typeof entry.original_words !== 'string') fail('INVALID_ENTRY','original_words must be a string');
  if ('corrects' in entry && !isUuid7(entry.corrects)) fail('INVALID_ENTRY','Correction reference must be UUIDv7');
  if (!jsonValue(entry)) fail('INVALID_ENTRY','Entry must contain only JSON values');
}
function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
  if (plain(value)) return `{${Object.keys(value).sort().map(key => `${JSON.stringify(key)}:${canonical(value[key])}`).join(',')}}`;
  return JSON.stringify(value);
}
async function statOrMissing(location) {
  try { return await lstat(location); } catch (error) { if (error.code === 'ENOENT') return null; throw error; }
}
async function safeDirectory(location, required = false) {
  const resolved = path.resolve(location);
  const parsed = path.parse(resolved);
  let current = parsed.root;
  for (const piece of resolved.slice(parsed.root.length).split(path.sep).filter(Boolean)) {
    current = path.join(current,piece);
    const stat = await statOrMissing(current);
    if (!stat) { if (required) fail('MISSING_ROOT',`Directory does not exist: ${current}`); return false; }
    if (stat.isSymbolicLink() || !stat.isDirectory()) fail('UNSAFE_PATH',`Expected a real directory without symlinks: ${current}`);
  }
  return true;
}
async function locations(input) {
  if (!plain(input) || typeof input.projectsRoot !== 'string' || !path.isAbsolute(input.projectsRoot)) fail('INVALID_ROOT','projectsRoot must be an explicit absolute directory');
  if ('dryRun' in input && typeof input.dryRun !== 'boolean') fail('INVALID_INPUT','dryRun must be boolean');
  await safeDirectory(input.projectsRoot,true);
  const directory = path.join(path.resolve(input.projectsRoot),'.daily-tasks');
  await safeDirectory(directory);
  const archive = path.join(directory,'archives');
  await safeDirectory(archive);
  return {directory,archive,lock:path.join(directory,'.decision-log.lock')};
}
async function assertUnlocked(lock) {
  if (await statOrMissing(lock)) fail('LOG_LOCKED',`Decision log lock exists at ${lock}. Retry later; after an interrupted process, explicitly verify its owner has stopped before recovering this lock. It is never broken automatically.`);
}
async function withAccess(input, callback) {
  const dirs = await locations(input);
  if (input.dryRun) {
    await assertUnlocked(dirs.lock);
    const result = await callback(dirs);
    await assertUnlocked(dirs.lock);
    return result;
  }
  await mkdir(dirs.directory,{recursive:true});
  await safeDirectory(dirs.directory,true);
  let acquired = false;
  for (let attempt=0;attempt<100;attempt++) {
    try { await mkdir(dirs.lock); acquired=true; break; }
    catch (error) {
      if (error.code !== 'EEXIST') throw error;
      const stat = await statOrMissing(dirs.lock);
      if (!stat) continue;
      if (stat.isSymbolicLink() || !stat.isDirectory()) fail('UNSAFE_PATH',`Unsafe log lock: ${dirs.lock}`);
      await delay(50);
    }
  }
  if (!acquired) await assertUnlocked(dirs.lock);
  if (!acquired) fail('LOG_LOCKED',`Could not acquire ${dirs.lock}; retry the operation`);
  try {
    await writeNew(path.join(dirs.lock,'owner.json'),JSON.stringify({pid:process.pid,created_at:new Date().toISOString()}));
    return await callback(dirs);
  } finally {
    await unlink(path.join(dirs.lock,'owner.json')).catch(error => { if (error.code !== 'ENOENT') throw error; });
    await rmdir(dirs.lock);
  }
}
async function writeNew(location,bytes) {
  const handle = await open(location,'wx');
  try { await handle.writeFile(bytes,'utf8'); await handle.sync(); } finally { await handle.close(); }
}
async function atomicWrite(location,value) {
  const temporary = path.join(path.dirname(location),`.decision-${uuid7()}.tmp`);
  try { await writeNew(temporary,`${JSON.stringify(value,null,2)}\n`); await rename(temporary,location); }
  finally { await unlink(temporary).catch(error => { if (error.code !== 'ENOENT') throw error; }); }
}
async function filenames(directory) {
  if (!await safeDirectory(directory)) return [];
  const names = await readdir(directory);
  const sequence = name => Number(name.match(/-decisions-(\d+)\.json$/)?.[1] ?? 0);
  return names.filter(name=>filenamePattern.test(name))
    .sort((a,b)=>a.slice(0,10).localeCompare(b.slice(0,10)) || sequence(a)-sequence(b))
    .map(name=>path.join(directory,name));
}
async function history(dirs) {
  const activeFiles = await filenames(dirs.directory);
  if (activeFiles.length>1) fail('CORRUPT_LOG','Multiple active decision files; explicit recovery required');
  const files=[...await filenames(dirs.archive),...activeFiles];
  const entries=[]; const ids=new Map(); const operations=new Map(); let active=null;
  for (const file of files) {
    const stat=await lstat(file);
    if (stat.isSymbolicLink() || !stat.isFile()) fail('UNSAFE_PATH',`Expected a regular decision file: ${file}`);
    let data;
    try {
      data=JSON.parse(await readFile(file,'utf8'));
      if (!plain(data) || data.schema_version !== 1 || !utc(data.created_at) || !Array.isArray(data.entries) || Object.keys(data).some(key=>!['schema_version','created_at','entries'].includes(key))) throw new Error('Invalid envelope');
      for (const entry of data.entries) validateEntry(entry);
    } catch (error) { fail('CORRUPT_LOG',`Corrupt decision log ${file}: ${error.message}`); }
    for (const entry of data.entries) {
      if (ids.has(entry.id) || operations.has(entry.operation_id)) fail('CORRUPT_LOG',`Duplicate decision or operation ID in ${file}`);
      ids.set(entry.id,entry); operations.set(entry.operation_id,entry); entries.push(entry);
    }
    if (activeFiles.includes(file)) active={file,data};
  }
  for (const entry of entries) if (entry.corrects && (entry.corrects===entry.id || !ids.has(entry.corrects))) fail('CORRUPT_LOG',`Invalid correction reference in ${entry.id}`);
  return {files,entries,ids,operations,active};
}
function nextFile(dirs, loaded) {
  const date=new Date().toISOString().slice(0,10).replaceAll('-','.');
  const names=new Set(loaded.files.map(file=>path.basename(file)));
  for (let n=0;n<=999999;n++) {
    const name=`${date}-decisions${n?`-${String(n).padStart(6,'0')}`:''}.json`;
    if (!names.has(name)) return path.join(dirs.directory,name);
  }
  fail('LOG_CAPACITY','No unused log filename available for today');
}

export async function appendDecision(input) {
  validateEntry(input?.entry);
  // Freeze the submitted JSON value before awaiting filesystem access.
  const entry=JSON.parse(JSON.stringify(input.entry));
  return withAccess(input,async dirs=>{
    const loaded=await history(dirs);
    const previous=loaded.operations.get(entry.operation_id);
    if (previous) {
      if (canonical(previous)!==canonical(entry)) fail('OPERATION_CONFLICT','Conflicting reuse of operation_id');
      return {entry:previous,duplicate:true,dryRun:input.dryRun===true};
    }
    if (loaded.ids.has(entry.id)) fail('DUPLICATE_ID','Decision ID already exists');
    if (entry.corrects && !loaded.ids.has(entry.corrects)) fail('INVALID_CORRECTION','Correction must reference a prior decision');
    if (entry.action === 'workspace.migration') {
      const { assertMigrationDecision } = await import('../operations/verification.mjs');
      await assertMigrationDecision(input,entry);
    }
    const file=loaded.active?.file ?? nextFile(dirs,loaded);
    const data=loaded.active?.data ?? {schema_version:1,created_at:new Date().toISOString(),entries:[]};
    data.entries.push(entry);
    if (!input.dryRun) await atomicWrite(file,data);
    return {entry,duplicate:false,file,dryRun:input.dryRun===true};
  });
}

export async function queryDecisions(input) {
  const limit=input?.limit ?? 100; const offset=input?.offset ?? 0;
  if (!Number.isInteger(limit) || limit<1 || limit>1000) fail('INVALID_QUERY','limit must be between 1 and 1000');
  if (!Number.isSafeInteger(offset) || offset<0) fail('INVALID_QUERY','offset must be a nonnegative safe integer');
  if (input?.recordId !== undefined && !isUuid7(input.recordId)) fail('INVALID_QUERY','recordId must be UUIDv7');
  if (input?.action !== undefined && (typeof input.action !== 'string' || !input.action.trim())) fail('INVALID_QUERY','action must be a nonempty string');
  for (const key of ['since','until']) if (input?.[key] !== undefined && !utc(input[key])) fail('INVALID_QUERY',`${key} must be a GMT timestamp`);
  if (input?.since && input?.until && Date.parse(input.since)>Date.parse(input.until)) fail('INVALID_QUERY','since must not be later than until');
  return withAccess(input,async dirs=>{
    const {entries}=await history(dirs);
    const matches=entries.filter(entry=>(!input.recordId || entry.record_ids.includes(input.recordId)) && (!input.action || entry.action===input.action) && (!input.since || Date.parse(entry.recorded_at)>=Date.parse(input.since)) && (!input.until || Date.parse(entry.recorded_at)<=Date.parse(input.until)));
    return {entries:matches.slice(offset,offset+limit),total:matches.length,offset,limit,nextOffset:offset+limit<matches.length?offset+limit:null};
  });
}

export async function archiveDecisions(input) {
  return withAccess(input,async dirs=>{
    const loaded=await history(dirs);
    if (!loaded.active) return {archived:false,dryRun:input.dryRun===true};
    const destination=path.join(dirs.archive,path.basename(loaded.active.file));
    if (await statOrMissing(destination)) fail('ARCHIVE_CONFLICT',`Archive already exists: ${destination}`);
    if (!input.dryRun) {
      await mkdir(dirs.archive,{recursive:true}); await safeDirectory(dirs.archive,true);
      // One same-volume rename preserves old bytes, including on an interrupted rotation.
      await rename(loaded.active.file,destination);
    }
    return {archived:true,file:destination,source:loaded.active.file,dryRun:input.dryRun===true};
  });
}
