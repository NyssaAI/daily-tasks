import { readFile, writeFile, mkdir, lstat } from 'node:fs/promises';
import path from 'node:path';
import { utcTimestamp } from '../time/time.mjs';

/**
 * Check if an automatic source scan is due for the given local day.
 * Returns true if no receipt exists at <stateRoot>/source-scans/<localDay>.json.
 */
export async function isScanDue(stateRoot, localDay) {
  if (!stateRoot || !localDay) throw new TypeError('stateRoot and localDay are required');
  const receiptPath = path.join(stateRoot, 'source-scans', `${localDay}.json`);
  try {
    const stat = await lstat(receiptPath);
    return !stat.isFile();
  } catch (error) {
    if (error.code === 'ENOENT') return true;
    throw error;
  }
}

/**
 * Record a deterministic daily scan receipt at <stateRoot>/source-scans/<localDay>.json.
 */
export async function recordScanReceipt(stateRoot, localDay, details = {}) {
  if (!stateRoot || !localDay) throw new TypeError('stateRoot and localDay are required');
  const dir = path.join(stateRoot, 'source-scans');
  await mkdir(dir, { recursive: true });
  const receiptPath = path.join(dir, `${localDay}.json`);
  const now = details.now ? utcTimestamp(details.now) : utcTimestamp(new Date().toISOString());
  const payload = {
    schemaVersion: 1,
    date: localDay,
    completedAt: now,
    sourcesScanned: details.sourcesScanned ?? [],
    candidatesCount: details.candidatesCount ?? 0,
  };
  await writeFile(receiptPath, JSON.stringify(payload, null, 2) + '\n', 'utf8');
  return payload;
}
