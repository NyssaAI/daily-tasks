import { lstat, mkdir, readFile, writeFile, rename, unlink, open, link } from 'node:fs/promises';
import { createHash, randomUUID } from 'node:crypto';
import path from 'node:path';

export const storageHash = text => text === null ? null : createHash('sha256').update(text).digest('hex');

/** Configuration snapshots use JSON; this feature never authors Markdown files. */
export async function readTemplateFile(filename) {
  const directories = [];
  for (let directory = path.dirname(filename); ; directory = path.dirname(directory)) {
    directories.push(directory);
    if (directory === path.dirname(directory)) break;
  }
  for (const directory of directories.reverse()) {
    try {
      const stat = await lstat(directory);
      if (!stat.isDirectory() || stat.isSymbolicLink()) throw new Error(`Unsafe template directory: ${directory}`);
    } catch (error) { if (error.code !== 'ENOENT') throw error; }
  }
  try {
    const stat = await lstat(filename);
    if (!stat.isFile() || stat.isSymbolicLink()) throw new Error(`Unsafe template file: ${filename}`);
    return await readFile(filename,'utf8');
  } catch (error) { if (error.code === 'ENOENT') return null; throw error; }
}

export async function readTemplateStore(directory) {
  const filename = path.join(directory,'templates/updates.json');
  const text = await readTemplateFile(filename);
  const value = text === null ? {schemaVersion:1,templates:{}} : JSON.parse(text);
  if (value.schemaVersion !== 1 || !value.templates || typeof value.templates !== 'object' || Array.isArray(value.templates)) throw new Error(`Invalid template store: ${filename}`);
  return {path:filename,sha256:storageHash(text),value};
}

export async function writeTemplateStore(store,value) {
  await readTemplateFile(store.path);
  await mkdir(path.dirname(store.path),{recursive:true});
  await readTemplateFile(store.path);
  const temporary = `${store.path}.${randomUUID()}.tmp`;
  try {
    await writeFile(temporary,JSON.stringify(value,null,2)+'\n',{flag:'wx'});
    if (storageHash(await readTemplateFile(store.path)) !== store.sha256) throw new Error('Template choices changed before save; prepare again');
    await rename(temporary,store.path);
  } finally { await unlink(temporary).catch(error => { if (error.code !== 'ENOENT') throw error; }); }
  store.value = value;
  store.sha256 = storageHash(await readTemplateFile(store.path));
}

/** Publish complete owner metadata atomically; existing locks require deliberate recovery. */
export async function withTemplateLock(store,callback) {
  const filename = path.join(path.dirname(store.path),'.updates.lock');
  await readTemplateFile(filename);
  await mkdir(path.dirname(filename),{recursive:true});
  await readTemplateFile(filename);
  const temporary = `${filename}.${randomUUID()}.tmp`;
  const lock = JSON.stringify({pid:process.pid,id:randomUUID()});
  let acquired = false;
  try {
    const handle = await open(temporary,'wx');
    try { await handle.writeFile(lock); await handle.sync(); }
    finally { await handle.close(); }
    try { await link(temporary,filename); acquired = true; }
    catch (error) {
      if (error.code === 'EEXIST') throw new Error(`Template choices locked at ${filename}. Locks are never removed automatically; confirm the owner stopped and exclude concurrent writers/recovery before deliberately removing only this lock, then retry.`);
      throw error;
    }
    await unlink(temporary);
    return await callback();
  } finally {
    if (acquired && await readTemplateFile(filename) === lock) await unlink(filename);
    await unlink(temporary).catch(error => { if (error.code !== 'ENOENT') throw error; });
  }
}
