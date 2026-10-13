import test from 'node:test';
import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { mkdir, mkdtemp, readFile, realpath, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { promisify } from 'node:util';
import { warmProjectIndex } from '../lib/inventory/warm.mjs';
import { buildPrewarmAutomation, prewarmDeclarationKey } from '../adapters/openclaw/automation.mjs';

const exec = promisify(execFile);
const id = n => `019a1234-5678-7abc-8def-${String(n).padStart(12,'0')}`;
const now = '2026-10-13T12:00:00.000Z';
const record = (n,type,title,extra='') => `---
id: ${id(n)}
type: ${type}
title: "${title}"
owner: owner@example.test
${type}-state: not-started
created_at: ${now}
updated_at: ${now}
${extra}---
# ${title}
`;

async function fixture() {
  await mkdir('.temp',{recursive:true});
  const root = await realpath(await mkdtemp(path.resolve('.temp/prewarm-')));
  const homeRoot = path.join(root,'home'), vaultRoot = path.join(root,'vault');
  const settings = path.join(vaultRoot,'.nyssa-ai/daily-tasks');
  const project = path.join(vaultRoot,'1-projects/alpha');
  const daily = path.join(vaultRoot,'2-areas/daily-plans');
  for (const directory of [homeRoot,settings,project,daily]) await mkdir(directory,{recursive:true});
  await writeFile(path.join(settings,'profile.json'),JSON.stringify({
    schema_version:2,
    user:{name:'Owner',email:'owner@example.test'},
    timezone:'UTC',
    vaultRoot:'.',
    projectsRoot:'./1-projects',
    dailyPlansRelative:'2-areas/daily-plans',
    projectIndex:{ttlSeconds:14400},
  }));
  await writeFile(path.join(project,'project-index.md'),record(1,'project','Alpha'));
  return {root,homeRoot,vaultRoot,project};
}

test('portable warm resolves configured context, rebuilds cold and reuses fresh without returning inventory', async () => {
  const input = await fixture();
  const cold = await warmProjectIndex({...input,now});
  assert.equal(cold.status,'rebuilt');
  assert.equal(cold.metrics.sourceReads,1);
  assert.equal(cold.counts.projects,1);
  assert.equal(Object.hasOwn(cold,'inventory'),false);
  const fresh = await warmProjectIndex({...input,now:'2026-10-13T13:00:00.000Z'});
  assert.equal(fresh.status,'reused');
  assert.equal(fresh.metrics.sourceReads,0);
  await writeFile(path.join(input.project,'task.md'),record(2,'task','Task',`project_id: ${id(1)}
milestone_id: ${id(3)}
`));
  const changed = await warmProjectIndex({...input,now:'2026-10-13T13:01:00.000Z'});
  assert.equal(changed.status,'rebuilt');
  assert.equal(changed.metrics.sourceReads,2);
  const expired = await warmProjectIndex({...input,now:'2026-10-13T17:01:00.000Z'});
  assert.equal(expired.status,'rebuilt');
});

test('portable CLI is independent of cwd, compact, and rejects missing explicit vault scope', async () => {
  const input = await fixture();
  const command = path.resolve('bin/warm-project-index.mjs');
  const help = JSON.parse((await exec(process.execPath,[command,'--help'],{cwd:input.root})).stdout);
  assert.equal(help.name,'warm-project-index');
  assert.match(help.effect,/never forces refresh/);
  const dry = JSON.parse((await exec(process.execPath,[command,'--vault-root',input.vaultRoot,'--home-root',input.homeRoot,'--dry-run'],{cwd:input.root})).stdout);
  assert.equal(dry.status,'preview');
  await assert.rejects(readFile(path.join(input.vaultRoot,'.temp/daily-tasks/project-index.json'),'utf8'),error => {
    assert.equal(error.code,'ENOENT');
    return true;
  });
  const {stdout} = await exec(process.execPath,[command,'--vault-root',input.vaultRoot,'--home-root',input.homeRoot],{cwd:input.root});
  const result = JSON.parse(stdout);
  assert.ok(['rebuilt','reused'].includes(result.status));
  assert.equal(Object.hasOwn(result,'inventory'),false);
  await assert.rejects(exec(process.execPath,[command],{cwd:input.root}),error => {
    assert.match(error.stderr,/--vault-root requires an absolute path/);
    return true;
  });
});

test('OpenClaw declaration is hourly by default, exact-argv, silent, idempotent, and configurable', async () => {
  const input = await fixture();
  const base = {
    vaultRoot:input.vaultRoot,
    homeRoot:input.homeRoot,
    every:'1h',
    nodePath:process.execPath,
    warmCommandPath:path.resolve('bin/warm-project-index.mjs'),
    gatewayPort:19091,
  };
  const first = buildPrewarmAutomation(base);
  const second = buildPrewarmAutomation(base);
  assert.equal(first.declarationKey,second.declarationKey);
  assert.equal(prewarmDeclarationKey(base),first.declarationKey);
  assert.equal(first.every,'1h');
  assert.equal(first.delivery,'none');
  assert.equal(first.usesAgent,false);
  assert.deepEqual(first.commandArgv.slice(0,2),[process.execPath,path.resolve('bin/warm-project-index.mjs')]);
  assert.ok(first.args.includes('--command-argv'));
  assert.deepEqual(first.args.slice(0,4),['automations','--port','19091','add']);
  assert.ok(first.args.includes('--no-deliver'));
  assert.ok(!first.args.includes('--message'));
  assert.equal(buildPrewarmAutomation({...base,every:'30m'}).every,'30m');
  assert.deepEqual(
    buildPrewarmAutomation({...base,gatewayPort:undefined,gatewayUrl:'wss://gateway.example.test'}).args.slice(0,4),
    ['automations','--url','wss://gateway.example.test','add'],
  );
  assert.throws(() => buildPrewarmAutomation({...base,every:'hourly'}),/every must be/);
  assert.throws(() => buildPrewarmAutomation({...base,every:'0h'}),/every must be/);
  assert.throws(() => buildPrewarmAutomation({...base,gatewayPort:70000}),/gatewayPort must be/);
  assert.throws(() => buildPrewarmAutomation({...base,gatewayPort:undefined,gatewayUrl:'https://gateway.example.test'}),/gatewayUrl must be/);
});

test('concurrent warm attempts preserve a valid reusable cache', async () => {
  const input = await fixture();
  const results = await Promise.all([
    warmProjectIndex({...input,now}),
    warmProjectIndex({...input,now}),
  ]);
  assert.ok(results.every(result => ['rebuilt','reused'].includes(result.status)));
  const cache = JSON.parse(await readFile(path.join(input.vaultRoot,'.temp/daily-tasks/project-index.json'),'utf8'));
  assert.equal(cache.projects.length,1);
  assert.equal((await warmProjectIndex({...input,now:'2026-10-13T13:00:00.000Z'})).status,'reused');
});
