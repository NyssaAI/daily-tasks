import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdir, mkdtemp, readFile } from 'node:fs/promises';
import { realpath } from 'node:fs/promises';
import path from 'node:path';
import { isScanDue, recordScanReceipt } from '#core/inventory/source-scans.mjs';

test('source-scans checks and writes deterministic daily receipts', async () => {
  await mkdir('.temp', { recursive: true });
  const stateRoot = await realpath(await mkdtemp(path.resolve('.temp/source-scans-')));
  const day = '2026.10.15';

  assert.equal(await isScanDue(stateRoot, day), true);

  const receipt = await recordScanReceipt(stateRoot, day, {
    sourcesScanned: ['inbox', 'mcp:email'],
    candidatesCount: 3,
  });

  assert.equal(receipt.date, day);
  assert.equal(receipt.candidatesCount, 3);
  assert.equal(await isScanDue(stateRoot, day), false);

  const saved = JSON.parse(await readFile(path.join(stateRoot, 'source-scans', `${day}.json`), 'utf8'));
  assert.equal(saved.schemaVersion, 1);
  assert.equal(saved.date, day);
  assert.deepEqual(saved.sourcesScanned, ['inbox', 'mcp:email']);
  assert.equal(saved.candidatesCount, 3);
});
