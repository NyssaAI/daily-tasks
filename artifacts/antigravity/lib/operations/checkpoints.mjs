import { readFile, readdir, lstat } from 'node:fs/promises';
import path from 'node:path';

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
