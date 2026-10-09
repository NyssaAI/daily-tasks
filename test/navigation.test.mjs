import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, realpath, mkdir, writeFile, rm, symlink } from 'node:fs/promises';
import path from 'node:path';
import { inspectNavigation } from '../lib/records/navigation.mjs';

async function fixture(t) {
  await mkdir(path.resolve('.temp'),{recursive:true});
  const root = await realpath(await mkdtemp(path.join(path.resolve('.temp'),'navigation-')));
  t.after(()=>rm(root,{recursive:true,force:true}));
  await mkdir(path.join(root,'project','milestone','inputs'),{recursive:true});
  return root;
}
test('navigation inspects criterion evidence, attachments and heading anchors without scanning holding areas or log',async t=>{
  const projectsRoot = await fixture(t);
  const source = path.join(projectsRoot,'project','milestone','t1-work.md');
  await writeFile(source,'---\ntype: task\n---\n# Work\n## Definition of Done\n- [x] [[evidence#Result]] and [file](inputs/result.txt)\n[[evidence#absent]]\n[missing](inputs/missing.pdf)\n[web](https://example.test)\n```\n[[fake]]\n```');
  await writeFile(path.join(path.dirname(source),'evidence.md'),'# Evidence\n## Result\n');
  await writeFile(path.join(path.dirname(source),'inputs','result.txt'),'verified');
  await writeFile(path.join(path.dirname(source),'inputs','t9-hidden.md'),'[[missing]]');
  await mkdir(path.join(projectsRoot,'.daily-tasks'));
  await writeFile(path.join(projectsRoot,'.daily-tasks','bad.md'),'[[missing]]');
  const result = await inspectNavigation({projectsRoot});
  assert.equal(result.records.length,1);
  assert.equal(result.checkedLinks,4);
  assert.deepEqual(result.diagnostics.map(item=>item.code),['missing-heading','missing-link-target']);
  assert.equal(result.diagnostics[0].source,source);
});
test('navigation rejects traversal and symlink targets and inspects explicit daily plan roots',async t=>{
  const projectsRoot = await fixture(t);
  const dailyPlansRoot = path.join(projectsRoot,'plans');
  await mkdir(dailyPlansRoot);
  await writeFile(path.join(dailyPlansRoot,'2026.10.09-daily-plan.md'),'[[../../escape]]\n[[../.daily-tasks/secret]]');
  const result = await inspectNavigation({projectsRoot,dailyPlansRoot});
  assert.deepEqual(result.diagnostics.map(item=>item.code),['unsafe-link','unsafe-link']);
  const linked = path.join(projectsRoot,'linked');
  try { await symlink(dailyPlansRoot,linked,'junction'); }
  catch (error) { if (['EPERM','EACCES'].includes(error.code)) return; throw error; }
  await assert.rejects(inspectNavigation({projectsRoot}),/Symbolic link/);
});

test('navigation checks reference-style images and links, titled destinations and escaped wiki aliases',async t=>{
  const projectsRoot = await fixture(t), directory = path.join(projectsRoot,'project','milestone');
  await writeFile(path.join(directory,'t1-work.md'),'---\ntype: task\n---\n[proof][p]\n![output][missing]\n[p]: <evidence.md#Result> "Reviewed"\n[missing]: inputs/missing.pdf\n[inline](<evidence.md#Result> "Title")\n[[evidence\\|Evidence]]\n');
  await writeFile(path.join(directory,'evidence.md'),'# Evidence\n## Result\n');
  const result = await inspectNavigation({projectsRoot});
  assert.deepEqual(result.diagnostics.map(issue=>issue.code),['missing-link-target']);
  assert.ok(result.targets.some(target=>target.path.endsWith('evidence.md') && target.sha256));
});
