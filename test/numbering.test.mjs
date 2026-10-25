import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, realpath, mkdir, writeFile, rm } from 'node:fs/promises';
import path from 'node:path';
import { nextRecordNumber } from '#core/records/numbering.mjs';
import { uuid7 } from '#core/identity/identity.mjs';

async function fixture(t) {
  await mkdir(path.resolve('.temp'), { recursive: true });
  const projectsRoot = await realpath(await mkdtemp(path.join(path.resolve('.temp'), 'numbering-')));
  t.after(() => rm(projectsRoot, { recursive: true, force: true }));
  const parentId = uuid7();
  await writeFile(path.join(projectsRoot, 'milestone.md'), `---\nid: ${parentId}\ntype: milestone\n---\n# Milestone\n`);
  return { projectsRoot, parentId, type: 'task' };
}

test('allocator retains live and cancelled labels and scopes live records to their parent', async t => {
  const input = await fixture(t);
  await writeFile(path.join(input.projectsRoot, 't4-cancelled.md'), `---\nid: ${uuid7()}\ntype: task\nmilestone_id: ${input.parentId}\ntask-state: cancelled\n---\n`);
  await writeFile(path.join(input.projectsRoot, 't7-active.md'), `---\nid: ${uuid7()}\ntype: task\nmilestone_id: ${input.parentId}\ntask-state: not-started\n---\n`);
  await writeFile(path.join(input.projectsRoot, 't99-other.md'), `---\nid: ${uuid7()}\ntype: task\nmilestone_id: ${uuid7()}\n---\n`);
  const result = await nextRecordNumber(input);
  assert.equal(result.number, 8);
  assert.deepEqual(result.usedNumbers, [4, 7]);
  assert.deepEqual(result.diagnostics, []);
});

test('unnumbered and malformed numeric labels block allocation', async t => {
  const input = await fixture(t);
  for (const [name, version] of [['unnumbered.md', 'record_version: 2\n'], ['legacy-task.md', ''], ['t0-invalid.md', '']]) {
    const filename = path.join(input.projectsRoot, name);
    await writeFile(filename, `---\nid: ${uuid7()}\ntype: task\nmilestone_id: ${input.parentId}\n${version}---\n`);
    const result = await nextRecordNumber(input);
    assert.equal(result.number, null);
    assert.ok(result.diagnostics.some(item => item.code === 'invalid-numbering-label'));
    await rm(filename);
  }
});

test('duplicate live numeric labels and missing parent block allocation', async t => {
  const input = await fixture(t);
  const sub1 = path.join(input.projectsRoot, 'sub1');
  const sub2 = path.join(input.projectsRoot, 'sub2');
  await mkdir(sub1);
  await mkdir(sub2);
  await writeFile(path.join(sub1, 't1-first.md'), `---\nid: ${uuid7()}\ntype: task\nmilestone_id: ${input.parentId}\n---\n`);
  await writeFile(path.join(sub2, 't1-second.md'), `---\nid: ${uuid7()}\ntype: task\nmilestone_id: ${input.parentId}\n---\n`);
  const duplicateResult = await nextRecordNumber(input);
  assert.equal(duplicateResult.number, null);
  assert.ok(duplicateResult.diagnostics.some(item => item.code === 'duplicate-numbering-label'));

  const missingParent = await nextRecordNumber({ ...input, parentId: uuid7() });
  assert.equal(missingParent.number, null);
  assert.ok(missingParent.diagnostics.some(item => item.code === 'invalid-numbering-parent'));
});
