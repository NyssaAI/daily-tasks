import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, realpath, readFile, readdir, rm, writeFile, mkdir, rename, symlink } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { appendDecision, archiveDecisions } from '#core/log/decision-log.mjs';
import { uuid7 } from '#core/identity/identity.mjs';

const makeEntry = (overrides = {}) => ({
  id: uuid7(),
  operation_id: uuid7(),
  action: 'task.accepted',
  record_ids: [uuid7()],
  actor: { kind: 'person', id: 'user@example.test' },
  activity_at: '2026-10-05T14:00:00Z',
  recorded_at: '2026-10-05T14:30:00Z',
  time_defaulted: false,
  ...overrides,
});

// macOS temporary paths can contain /var, a symlink; log roots must use the real directory.
async function fixture(t) {
  const root = await realpath(await mkdtemp(path.join(tmpdir(), 'daily-log-')));
  t.after(() => rm(root, { recursive: true, force: true }));
  return root;
}

test('write-only append writes directly to end of active log and archive moves segment', async t => {
  const projectsRoot = await fixture(t);
  const entry = makeEntry();
  const first = await appendDecision({ projectsRoot, entry });
  assert.equal(first.duplicate, false);
  const bytes = await readFile(first.file, 'utf8');
  assert.deepEqual(JSON.parse(bytes.trim()), entry);
  const archived = await archiveDecisions({ projectsRoot });
  assert.equal(await readFile(archived.file, 'utf8'), bytes);
  const correction = makeEntry({ corrects: entry.id });
  const second = await appendDecision({ projectsRoot, entry: correction });
  assert.notEqual(second.file, first.file);
  assert.deepEqual(JSON.parse((await readFile(second.file, 'utf8')).trim()), correction);
});

test('dry runs never create storage or modify existing bytes', async t => {
  const projectsRoot = await fixture(t);
  const entry = makeEntry();
  await appendDecision({ projectsRoot, entry, dryRun: true });
  await archiveDecisions({ projectsRoot, dryRun: true });
  assert.deepEqual(await readdir(projectsRoot), []);
  const first = await appendDecision({ projectsRoot, entry });
  const bytes = await readFile(first.file, 'utf8');
  await archiveDecisions({ projectsRoot, dryRun: true });
  await appendDecision({ projectsRoot, entry: makeEntry(), dryRun: true });
  assert.equal(await readFile(first.file, 'utf8'), bytes);
});

test('invalid input fails without writing to disk, while append does not read existing bytes', async t => {
  const projectsRoot = await fixture(t);
  await assert.rejects(appendDecision({ projectsRoot, entry: makeEntry({ recorded_at: '2026-02-30T00:00:00Z' }) }), /time|timestamp/i);
  await assert.rejects(appendDecision({ projectsRoot, entry: makeEntry({ actor: { kind: 'person', id: '' } }) }), /actor/i);
  const first = await appendDecision({ projectsRoot, entry: makeEntry() });
  await writeFile(first.file, '{"unparsed_prior_line":true}\n');
  const next = makeEntry();
  await appendDecision({ projectsRoot, entry: next });
  const lines = (await readFile(first.file, 'utf8')).trim().split('\n');
  assert.equal(lines.length, 2);
  assert.deepEqual(JSON.parse(lines[1]), next);
});

test('person actors require email identity while named agents remain valid', async t => {
  const projectsRoot = await fixture(t);
  await assert.rejects(appendDecision({ projectsRoot, entry: makeEntry({ actor: { kind: 'person', id: 'Alex Example' } }) }), /email/i);
  assert.deepEqual(await readdir(projectsRoot), []);
  const result = await appendDecision({ projectsRoot, entry: makeEntry({ actor: { kind: 'agent', id: 'release-reviewer' } }) });
  assert.equal(result.entry.actor.id, 'release-reviewer');
});

test('separate processes serialize appends without losing entries', async t => {
  const projectsRoot = await fixture(t);
  const moduleUrl = new URL('../src/core/log/decision-log.mjs', import.meta.url).href;
  await Promise.all(Array.from({ length: 8 }, () => new Promise((resolve, reject) => {
    const code = `import {appendDecision} from ${JSON.stringify(moduleUrl)}; await appendDecision(${JSON.stringify({ projectsRoot, entry: makeEntry() })});`;
    const child = spawn(process.execPath, ['--input-type=module', '-e', code]);
    let errors = '';
    child.stderr.on('data', x => errors += x);
    child.on('error', reject);
    child.on('close', c => c === 0 ? resolve() : reject(new Error(errors)));
  })));
  const logDir = path.join(projectsRoot, '.daily-tasks');
  const files = (await readdir(logDir)).filter(name => name.endsWith('.json'));
  const lines = (await readFile(path.join(logDir, files[0]), 'utf8')).trim().split('\n');
  assert.equal(lines.length, 8);
});

test('same-day rotations choose fresh names across archives', async t => {
  const projectsRoot = await fixture(t);
  const record = uuid7();
  const files = [];
  for (let i = 0; i < 3; i++) {
    const result = await appendDecision({ projectsRoot, entry: makeEntry({ record_ids: [record], action: i === 0 ? 'first' : 'later' }) });
    files.push(result.file);
    await archiveDecisions({ projectsRoot });
  }
  assert.equal(new Set(files).size, 3);
});

test('active file is reused across days until archived', async t => {
  const projectsRoot = await fixture(t);
  const entry = makeEntry();
  const first = await appendDecision({ projectsRoot, entry });
  const oldFile = path.join(path.dirname(first.file), '2020.01.01-decisions.json');
  await rename(first.file, oldFile);
  const next = await appendDecision({ projectsRoot, entry: makeEntry() });
  assert.equal(next.file, oldFile);
});

test('failed archive setup preserves original bytes', async t => {
  const projectsRoot = await fixture(t);
  const entry = makeEntry();
  const first = await appendDecision({ projectsRoot, entry });
  const bytes = await readFile(first.file, 'utf8');
  const archiveDir = path.join(projectsRoot, '.daily-tasks', 'archives');
  await writeFile(archiveDir, 'obstruction');
  await assert.rejects(archiveDecisions({ projectsRoot }), /directory/i);
  assert.equal(await readFile(first.file, 'utf8'), bytes);
  await rm(archiveDir);
});

test('stale locks are reported without mutation or automatic breaking', async t => {
  const projectsRoot = await fixture(t);
  const lock = path.join(projectsRoot, '.daily-tasks', '.decision-log.lock');
  await mkdir(lock, { recursive: true });
  await writeFile(path.join(lock, 'owner.json'), 'prior process');
  await assert.rejects(appendDecision({ projectsRoot, entry: makeEntry(), dryRun: true }), error => error.code === 'LOG_LOCKED' && error.message.includes(lock));
  assert.equal(await readFile(path.join(lock, 'owner.json'), 'utf8'), 'prior process');
});

test('symlinked storage cannot redirect log operations', async t => {
  const projectsRoot = await fixture(t);
  const elsewhere = await fixture(t);
  await symlink(elsewhere, path.join(projectsRoot, '.daily-tasks'), process.platform === 'win32' ? 'junction' : 'dir');
  await assert.rejects(appendDecision({ projectsRoot, entry: makeEntry() }), error => error.code === 'UNSAFE_PATH');
  assert.deepEqual(await readdir(elsewhere), []);
});
