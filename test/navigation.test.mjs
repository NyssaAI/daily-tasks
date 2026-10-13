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

test('extensionless wiki links with dotted date names resolve to Markdown files',async t=>{
  const projectsRoot = await fixture(t), directory = path.join(projectsRoot,'project','milestone');
  await writeFile(path.join(directory,'t1-work.md'),'---\ntype: task\n---\n[[2026.10.07-evidence|Dated evidence]]\n');
  await writeFile(path.join(directory,'2026.10.07-evidence.md'),'# Dated evidence\n');
  const result = await inspectNavigation({projectsRoot});
  assert.deepEqual(result.diagnostics,[]);
  assert.ok(result.targets.some(target=>target.path.endsWith('2026.10.07-evidence.md')));
});

test('vault-relative wiki links resolve outside the project collection when vaultRoot is explicit',async t=>{
  const projectsRoot = await fixture(t), directory = path.join(projectsRoot,'project','milestone');
  await mkdir(path.join(projectsRoot,'resources'));
  await writeFile(path.join(directory,'t1-work.md'),'---\ntype: task\n---\n[[resources/evidence|Vault evidence]]\n');
  await writeFile(path.join(projectsRoot,'resources/evidence.md'),'# Vault evidence\n');
  const result = await inspectNavigation({vaultRoot:projectsRoot,projectsRoot});
  assert.deepEqual(result.diagnostics,[]);
  assert.ok(result.targets.some(target=>target.path.endsWith(path.join('resources','evidence.md'))));
});

test('ordinary Markdown and wiki folder links coexist with specific file evidence',async t=>{
  const projectsRoot = await fixture(t), directory = path.join(projectsRoot,'project','milestone');
  await mkdir(path.join(directory,'outputs'));
  await mkdir(path.join(directory,'inputs','v1.0'));
  await mkdir(path.join(directory,'inputs','2026.10.13-notes'));
  await writeFile(path.join(directory,'inputs','proof.pdf'),'proof');
  await writeFile(path.join(directory,'t1-work.md'),'---\ntype: task\n---\n[Inputs](inputs/)\n[[outputs|Outputs]]\n[Version](inputs/v1.0)\n[[inputs/v1.0]]\n[[inputs/2026.10.13-notes]]\n## Definition of Done\n- [x] [Proof](inputs/proof.pdf)\n');
  const result = await inspectNavigation({projectsRoot});
  assert.deepEqual(result.diagnostics,[]);
  assert.equal(result.checkedLinks,6);
  assert.deepEqual(result.targets.map(target=>[path.relative(directory,target.path),target.kind,target.sha256]),[
    ['inputs','directory',null],['outputs','directory',null],[path.join('inputs','v1.0'),'directory',null],[path.join('inputs','2026.10.13-notes'),'directory',null],[path.join('inputs','proof.pdf'),'file',null]
  ]);
});

test('directories cannot supply headings or named required file evidence and missing files stay diagnostic',async t=>{
  const projectsRoot = await fixture(t), directory = path.join(projectsRoot,'project','milestone');
  await mkdir(path.join(directory,'inputs','proof.pdf'));
  await mkdir(path.join(directory,'inputs','proof.md'));
  await writeFile(path.join(directory,'t1-work.md'),'---\ntype: task\n---\n[Folder heading](inputs/#result)\n[[inputs#Result]]\n[Empty fragment](inputs/#)\n## Definition of Done\n- [x] [Proof](inputs/proof.pdf)\n- [x] [[inputs/proof.md]]\n- [x] [Missing](inputs/missing.pdf)\n- [x] [[inputs/missing.md]]\n');
  const result = await inspectNavigation({projectsRoot});
  assert.deepEqual(result.diagnostics.map(issue=>issue.code),[
    'invalid-link-target','invalid-link-target','invalid-link-target','invalid-link-target','invalid-link-target','missing-link-target','missing-link-target'
  ]);
  assert.ok(!result.targets.some(target=>/proof\.(pdf|md)$/.test(target.path)));
});

test('folder links preserve hidden, escaped and symlink target protection',async t=>{
  const projectsRoot = await fixture(t), directory = path.join(projectsRoot,'project','milestone');
  await mkdir(path.join(directory,'inputs','.hidden'));
  await writeFile(path.join(directory,'t1-work.md'),'---\ntype: task\n---\n[Hidden](inputs/.hidden/)\n[[inputs/.hidden]]\n[Escaped](../../../)\n[[../../../]]\n');
  const result = await inspectNavigation({projectsRoot});
  assert.deepEqual(result.diagnostics.map(issue=>issue.code),Array(4).fill('unsafe-link'));
  await symlink(path.join(directory,'inputs'),path.join(directory,'inputs','linked'),'junction');
  await writeFile(path.join(directory,'t1-work.md'),'---\ntype: task\n---\n[Linked](inputs/linked/)\n');
  assert.deepEqual((await inspectNavigation({projectsRoot})).diagnostics.map(issue=>issue.code),['unsafe-link']);
  await writeFile(path.join(directory,'t1-work.md'),'---\ntype: task\n---\n[[inputs/linked]]\n');
  assert.deepEqual((await inspectNavigation({projectsRoot})).diagnostics.map(issue=>issue.code),['unsafe-link']);
});

test('ordinary file attachments retain non-Markdown fragment diagnostics',async t=>{
  const projectsRoot = await fixture(t), directory = path.join(projectsRoot,'project','milestone');
  const attachment = path.join(directory,'inputs','proof.pdf');
  await writeFile(attachment,'proof');
  await writeFile(path.join(directory,'t1-work.md'),'---\ntype: task\n---\n[Proof](inputs/proof.pdf#page=1)\n');
  const result = await inspectNavigation({projectsRoot});
  assert.deepEqual(result.diagnostics.map(issue=>issue.code),['unverifiable-anchor']);
  assert.deepEqual(result.targets,[{path:attachment,kind:'file',sha256:null}]);
});

test('task and milestone criterion evidence requires files even without extensions or with trailing slashes',async t=>{
  for (const type of ['task','milestone']) {
    await t.test(type,async t=>{
      const projectsRoot = await fixture(t), directory = path.join(projectsRoot,'project','milestone');
      await mkdir(path.join(directory,'outputs'));
      const source = path.join(directory,type === 'task' ? 't1-work.md' : 'm1-work.md');
      const links = ['[[outputs]]','[Evidence folder](outputs/)','[[outputs/]]','[Evidence folder](outputs)'];
      await writeFile(source,`---\ntype: ${type}\n---\n${links.join('\n')}\n## Definition of Done\n${links.map(link=>`- [x] ${link}`).join('\n')}\n## Output\n${links.join('\n')}\n`);
      const result = await inspectNavigation({projectsRoot});
      assert.equal(result.checkedLinks,12);
      assert.deepEqual(result.diagnostics.map(({code,target})=>({code,target})),['outputs','outputs/','outputs/','outputs'].map(target=>({code:'invalid-link-target',target})));
      assert.deepEqual(result.targets,[{path:path.join(directory,'outputs'),kind:'directory',sha256:null}]);
    });
  }
});

test('extensionless criterion files pass while contextual and typed relationship links remain navigation',async t=>{
  const projectsRoot = await fixture(t), directory = path.join(projectsRoot,'project','milestone');
  await mkdir(path.join(directory,'outputs'));
  await writeFile(path.join(directory,'inputs','proof'),'proof');
  await writeFile(path.join(directory,'inputs','result.md'),'# Result\n');
  await writeFile(path.join(directory,'t2-related.md'),'---\ntype: task\n---\n# Related task\n');
  await writeFile(path.join(directory,'t1-work.md'),'---\ntype: task\n---\n- [x] [[outputs]]\n## Definition of Done\n- [x] [[outputs]]\n- [x] [[inputs/proof]] and [Proof](inputs/proof) and [[inputs/result]]\n### Depends on\n- [x] [[outputs]]\n- [[t2-related]] <!-- ref: 019a1234-5678-7abc-8def-000000000001 -->\n## Output\n- [x] [[outputs]]\n');
  const result = await inspectNavigation({projectsRoot});
  assert.deepEqual(result.diagnostics.map(({code,target})=>({code,target})),[{code:'invalid-link-target',target:'outputs'}]);
  assert.equal(result.targets.find(target=>target.path.endsWith('inputs/proof')).kind,'file');
  assert.equal(result.targets.find(target=>target.path.endsWith('inputs/result.md')).kind,'file');
  assert.ok(result.targets.some(target=>target.path.endsWith('t2-related.md')));
});

test('reference-style criterion evidence also requires regular files',async t=>{
  const projectsRoot = await fixture(t), directory = path.join(projectsRoot,'project','milestone');
  await mkdir(path.join(directory,'outputs'));
  await writeFile(path.join(directory,'inputs','proof'),'proof');
  await writeFile(path.join(directory,'t1-work.md'),'---\ntype: task\n---\n## Definition of Done\n- [x] [Evidence folder][folder] and ![Image][] and [Shortcut]\n- [x] [Proof][file]\n## Output\n[folder]: outputs/\n[image]: outputs\n[shortcut]: outputs/\n[file]: inputs/proof\n[ordinary]: outputs/\n');
  const result = await inspectNavigation({projectsRoot});
  assert.deepEqual(result.diagnostics.map(issue=>issue.code),Array(3).fill('invalid-link-target'));
  assert.deepEqual(result.targets,[{path:path.join(directory,'inputs','proof'),kind:'file',sha256:null},{path:path.join(directory,'outputs'),kind:'directory',sha256:null}]);
});

test('target resolution excludes hidden state, outside roots and symlink attachments for both link syntaxes',async t=>{
  const projectsRoot = await fixture(t), directory = path.join(projectsRoot,'project','milestone');
  const outside = await realpath(await mkdtemp(path.resolve('.temp/navigation-outside-')));
  t.after(()=>rm(outside,{recursive:true,force:true}));
  const hidden = path.join(projectsRoot,'.state','secret.md');
  await mkdir(path.dirname(hidden)); await writeFile(hidden,'# Secret');
  const external = path.join(outside,'secret.md'); await writeFile(external,'# Secret');
  const attachment = path.join(directory,'inputs','linked.md');
  await symlink(external,attachment);
  const relative = path.relative(directory,external).split(path.sep).join('/');
  await writeFile(path.join(directory,'t1-work.md'),`---\ntype: task\n---\n[[../../.state/secret]]\n[hidden](../../.state/secret.md)\n[[${relative}]]\n[outside](${relative})\n[[inputs/linked]]\n[symlink](inputs/linked.md)\n`);
  const result = await inspectNavigation({projectsRoot});
  assert.equal(result.diagnostics.length,6);
  assert.ok(result.diagnostics.every(issue=>issue.code === 'unsafe-link'));
  assert.ok(result.diagnostics.slice(0,4).every(issue=>issue.message === 'Target is outside allowed roots or inside hidden state'));
  assert.ok(result.diagnostics.slice(4).every(issue=>/Symbolic link excluded/.test(issue.message)));
  assert.deepEqual(result.targets,[]);
});
