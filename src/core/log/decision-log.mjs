import { lstat, mkdir, readdir, open, rename, unlink, rmdir } from 'node:fs/promises';
import path from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';
import { isUuid7 } from '../identity/identity.mjs';
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
  if ('corrects' in entry && (!isUuid7(entry.corrects) || entry.corrects === entry.id)) fail('INVALID_ENTRY','Correction reference must be a distinct UUIDv7');
  if (!jsonValue(entry)) fail('INVALID_ENTRY','Entry must contain only JSON values');
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
async function appendLine(location, line) {
  const stat = await statOrMissing(location);
  if (stat && (stat.isSymbolicLink() || !stat.isFile())) fail('UNSAFE_PATH',`Expected a regular decision file: ${location}`);
  const handle = await open(location, 'a');
  try { await handle.writeFile(line, 'utf8'); await handle.sync(); } finally { await handle.close(); }
}
async function filenames(directory) {
  if (!await safeDirectory(directory)) return [];
  const names = await readdir(directory);
  const sequence = name => Number(name.match(/-decisions-(\d+)\.json$/)?.[1] ?? 0);
  return names.filter(name=>filenamePattern.test(name))
    .sort((a,b)=>a.slice(0,10).localeCompare(b.slice(0,10)) || sequence(a)-sequence(b))
    .map(name=>path.join(directory,name));
}
async function resolveActiveFile(dirs) {
  const activeFiles = await filenames(dirs.directory);
  if (activeFiles.length > 1) fail('CORRUPT_LOG','Multiple active decision files; explicit recovery required');
  if (activeFiles.length === 1) {
    const file = activeFiles[0];
    const stat = await lstat(file);
    if (stat.isSymbolicLink() || !stat.isFile()) fail('UNSAFE_PATH',`Expected a regular decision file: ${file}`);
    return { active: file, file };
  }
  const archived = await filenames(dirs.archive);
  const date = new Date().toISOString().slice(0,10).replaceAll('-','.');
  const names = new Set(archived.map(file => path.basename(file)));
  for (let n = 0; n <= 999999; n++) {
    const name = `${date}-decisions${n ? `-${String(n).padStart(6,'0')}` : ''}.json`;
    if (!names.has(name)) return { active: null, file: path.join(dirs.directory, name) };
  }
  fail('LOG_CAPACITY','No unused log filename available for today');
}

/** Write-only decision log append. Validates entry shape and appends directly to the end of the active log file without reading history. */
export async function appendDecision(input) {
  validateEntry(input?.entry);
  const entry = JSON.parse(JSON.stringify(input.entry));
  return withAccess(input, async dirs => {
    const { file } = await resolveActiveFile(dirs);
    if (!input.dryRun) await appendLine(file, `${JSON.stringify(entry)}\n`);
    return { entry, duplicate: false, file, dryRun: input.dryRun === true };
  });
}

export async function archiveDecisions(input) {
  return withAccess(input, async dirs => {
    const { active } = await resolveActiveFile(dirs);
    if (!active) return { archived: false, dryRun: input.dryRun === true };
    const destination = path.join(dirs.archive, path.basename(active));
    if (await statOrMissing(destination)) fail('ARCHIVE_CONFLICT',`Archive already exists: ${destination}`);
    if (!input.dryRun) {
      await mkdir(dirs.archive,{recursive:true}); await safeDirectory(dirs.archive,true);
      await rename(active,destination);
    }
    return { archived: true, file: destination, source: active, dryRun: input.dryRun === true };
  });
}
