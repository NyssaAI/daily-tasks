import test from 'node:test';
import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { mkdir, mkdtemp, readFile, readdir, realpath, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { promisify } from 'node:util';
import { createHash } from 'node:crypto';
import { warmProjectIndex } from '#core/inventory/warm.mjs';
import { buildPrewarmAutomation, prewarmDeclarationKey } from '#adapters/openclaw/automation.mjs';
import { registerDailyTasksCli } from '#adapters/openclaw/cli.mjs';

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

async function layeredFixture() {
  const input = await fixture();
  const directory = path.join(input.root,'accepted settings with spaces');
  await mkdir(directory);
  const user = path.join(directory,'personal.json'), project = path.join(directory,'workspace.json');
  await writeFile(user,JSON.stringify({schema_version:2,user:{name:'Owner',email:'owner@example.test'},timezone:'UTC'}));
  await writeFile(project,JSON.stringify({schema_version:2,projectsRoot:'./1-projects',dailyPlansRelative:'2-areas/daily-plans'}));
  const stateRoot = path.join(input.root,'established state');
  await mkdir(stateRoot);
  await writeFile(path.join(stateRoot,'review.json'),JSON.stringify({preserved:true}));
  return {...input,stateRoot,configurationSources:{schemaVersion:1,user:{profilePath:user},project:{profilePath:project}}};
}

function setupAction(run) {
  let action;
  const program = {
    command() { return this; }, description() { return this; }, requiredOption() { return this; }, option() { return this; },
    action(callback) { action = callback; return this; },
  };
  registerDailyTasksCli({program,pluginRoot:path.resolve('.'),openclawEntry:path.resolve('openclaw-test.mjs'),run});
  return action;
}

test('layered context survives portable argv and native registration with its established state root', async () => {
  const input = await layeredFixture();
  const command = path.resolve('src/cli/warm-project-index.mjs');
  const before = await readFile(path.join(input.project,'project-index.md'),'utf8');
  const expected = await warmProjectIndex({...input,dryRun:true});
  const direct = JSON.parse((await exec(process.execPath,[command,'--vault-root',input.vaultRoot,'--home-root',input.homeRoot,
    '--configuration-sources',JSON.stringify(input.configurationSources),'--state-root',input.stateRoot,'--dry-run'],{cwd:input.root})).stdout);
  assert.equal(direct.planningBinding,expected.planningBinding);
  let registered;
  await setupAction(async (_entry,args) => { registered = args; return {id:'synthetic'}; })({
    ...input,configurationSources:JSON.stringify(input.configurationSources),every:'1h',disabled:true,
    preferenceOverrides:{timezone:'Asia/Tokyo'},now:'2000-01-01T00:00:00.000Z',localDate:'2000-01-01',profile:{secret:'excluded'},
  });
  const argv = JSON.parse(registered[registered.indexOf('--command-argv')+1]);
  assert.deepEqual(JSON.parse(argv[argv.indexOf('--configuration-sources')+1]),input.configurationSources);
  assert.equal(argv[argv.indexOf('--state-root')+1],input.stateRoot);
  assert.ok(registered.includes('--disabled'));
  assert.doesNotMatch(JSON.stringify(argv),/Asia\/Tokyo|2000-01-01|excluded|preferenceOverrides|localDate/);
  const actual = JSON.parse((await exec(argv[0],[...argv.slice(1),'--dry-run'],{cwd:input.homeRoot})).stdout);
  assert.equal(actual.planningBinding,expected.planningBinding);
  assert.deepEqual(actual.counts,expected.counts);
  assert.equal(await readFile(path.join(input.project,'project-index.md'),'utf8'),before);
  assert.deepEqual(JSON.parse(await readFile(path.join(input.stateRoot,'review.json'),'utf8')),{preserved:true});
});

test('prewarm keeps explicit source absences and canonical identities', async () => {
  const input = await layeredFixture();
  const base = {...input,every:'1h',nodePath:process.execPath,warmCommandPath:path.resolve('src/cli/warm-project-index.mjs')};
  const descriptor = {schemaVersion:1,user:{profilePath:null},project:{profilePath:path.join(input.vaultRoot,'.nyssa-ai/daily-tasks/profile.json')}};
  const first = buildPrewarmAutomation({...base,configurationSources:descriptor});
  const reordered = {project:{profilePath:descriptor.project.profilePath},user:{profilePath:null},schemaVersion:1};
  assert.equal(first.declarationKey,buildPrewarmAutomation({...base,configurationSources:reordered,every:'30m'}).declarationKey);
  assert.notEqual(first.declarationKey,buildPrewarmAutomation({...base,configurationSources:input.configurationSources}).declarationKey);
  assert.notEqual(first.declarationKey,buildPrewarmAutomation({...base,configurationSources:descriptor,stateRoot:path.join(input.root,'different state')}).declarationKey);
  if (process.platform === 'win32') assert.equal(first.declarationKey,buildPrewarmAutomation({...base,
    vaultRoot:base.vaultRoot.toUpperCase(),homeRoot:base.homeRoot.toUpperCase(),stateRoot:base.stateRoot.toUpperCase(),
    configurationSources:{...descriptor,project:{profilePath:descriptor.project.profilePath.toUpperCase()}},
  }).declarationKey);
  const homeSettings = path.join(input.homeRoot,'.nyssa-ai/daily-tasks');
  await mkdir(homeSettings,{recursive:true});
  await writeFile(path.join(homeSettings,'profile.json'),'malformed source that must remain absent');
  const actual = JSON.parse((await exec(first.commandArgv[0],[...first.commandArgv.slice(1),'--dry-run'],{cwd:input.root})).stdout);
  assert.equal(actual.counts.projects,1);
  const conventional = {vaultRoot:input.vaultRoot,homeRoot:input.homeRoot,every:'1h'};
  const normalized = value => process.platform === 'win32' ? path.normalize(value).toLowerCase() : path.normalize(value);
  const hash = createHash('sha256').update(JSON.stringify([normalized(conventional.vaultRoot),normalized(conventional.homeRoot),null])).digest('hex').slice(0,24);
  assert.equal(prewarmDeclarationKey(conventional),`daily-tasks:project-index-prewarm:${hash}`);
});

test('prewarm rejects invalid or missing durable selectors before registering', async () => {
  const input = await layeredFixture();
  let calls = 0;
  const action = setupAction(async () => { calls++; return {}; });
  const base = {vaultRoot:input.vaultRoot,homeRoot:input.homeRoot,every:'1h',stateRoot:input.stateRoot};
  const cases = [
    [{configurationSources:'{'},/JSON/],
    [{configurationSources:JSON.stringify({...input.configurationSources,user:{profilePath:path.join(input.root,'missing.json')}})},/source missing/],
    [{configurationSources:JSON.stringify({...input.configurationSources,user:{profilePath:'relative.json'}})},/absolute profilePath/],
    [{configurationSources:JSON.stringify({...input.configurationSources,extra:'invalid'})},/schemaVersion/],
  ];
  const canonicalState = path.join(input.vaultRoot,'.nyssa-ai/daily-tasks');
  await mkdir(canonicalState,{recursive:true});
  await writeFile(path.join(canonicalState,'review.json'),JSON.stringify({preserved:true}));
  cases.push([{stateRoot:path.join(input.root,'empty state')},/no authoritative history/]);
  for (const [change,expected] of cases) await assert.rejects(action({...base,...change}),expected);
  assert.equal(calls,0);
  const command = path.resolve('src/cli/warm-project-index.mjs');
  for (const [args,expected] of [
    [['--configuration-sources','{'],/JSON/],
    [['--unknown-flag'],/Unknown or duplicate argument/],
  ]) await assert.rejects(exec(process.execPath,[command,'--vault-root',input.vaultRoot,'--home-root',input.homeRoot,...args],{cwd:input.root}),error => {
    assert.match(error.stderr,expected); return true;
  });
});

test('new-form registration captures resolved state and dry-run does not register', async t => {
  const input = await fixture();
  const canonicalState = path.join(input.vaultRoot,'.nyssa-ai/daily-tasks');
  await mkdir(canonicalState,{recursive:true});
  await writeFile(path.join(canonicalState,'review.json'),JSON.stringify({preserved:true}));
  const configurationSources = {schemaVersion:1,user:{profilePath:null},project:{profilePath:path.join(input.vaultRoot,'.nyssa-ai/daily-tasks/profile.json')}};
  let calls = 0;
  const action = setupAction(async () => { calls++; return {}; });
  const output = [];
  t.mock.method(console,'log',value => output.push(JSON.parse(value)));
  await action({...input,configurationSources:JSON.stringify(configurationSources),every:'1h',dryRun:true});
  assert.equal(calls,0);
  assert.equal(output[0].status,'preview');
  assert.equal(output[0].commandArgv[output[0].commandArgv.indexOf('--state-root')+1],canonicalState);
  assert.deepEqual(JSON.parse(output[0].commandArgv[output[0].commandArgv.indexOf('--configuration-sources')+1]),configurationSources);
  await action({...input,every:'1h',dryRun:true});
  assert.equal(output[1].declarationKey,prewarmDeclarationKey({...input,every:'1h'}));
  assert.equal(output[1].commandArgv.includes('--state-root'),false);
  assert.equal(calls,0);
});

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
  const command = path.resolve('src/cli/warm-project-index.mjs');
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
    warmCommandPath:path.resolve('src/cli/warm-project-index.mjs'),
    gatewayPort:19091,
  };
  const first = buildPrewarmAutomation(base);
  const second = buildPrewarmAutomation(base);
  assert.equal(first.declarationKey,second.declarationKey);
  assert.equal(prewarmDeclarationKey(base),first.declarationKey);
  assert.equal(first.every,'1h');
  assert.equal(first.delivery,'none');
  assert.equal(first.usesAgent,false);
  assert.deepEqual(first.commandArgv.slice(0,2),[process.execPath,path.resolve('src/cli/warm-project-index.mjs')]);
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
  for (let round=0;round<5;round++) {
    const input = await fixture();
    const results = await Promise.allSettled(Array.from({length:8},() => warmProjectIndex({...input,now})));
    for (const result of results) {
      assert.equal(result.status,'fulfilled',result.reason?.stack);
      assert.ok(['rebuilt','reused'].includes(result.value.status));
    }
    const directory = path.join(input.vaultRoot,'.temp/daily-tasks');
    const cache = JSON.parse(await readFile(path.join(directory,'project-index.json'),'utf8'));
    assert.equal(cache.projects.length,1);
    assert.equal((await warmProjectIndex({...input,now:'2026-10-13T13:00:00.000Z'})).status,'reused');
    assert.deepEqual((await readdir(directory)).filter(name => name.endsWith('.tmp')),[]);
  }
});

test('separate warm processes preserve a reusable cache and remove temporary writes', async () => {
  const input = await fixture();
  const moduleUrl = new URL('../src/core/inventory/warm.mjs',import.meta.url).href;
  const source = 'const {warmProjectIndex} = await import(process.argv[1]); console.log(JSON.stringify(await warmProjectIndex(JSON.parse(process.argv[2]))));';
  const results = await Promise.allSettled(Array.from({length:8},() => exec(process.execPath,
    ['--input-type=module','-e',source,moduleUrl,JSON.stringify({...input,now})],{cwd:input.root})));
  for (const result of results) {
    assert.equal(result.status,'fulfilled',result.reason?.stack);
    assert.ok(['rebuilt','reused'].includes(JSON.parse(result.value.stdout).status));
  }
  assert.equal((await warmProjectIndex({...input,now:'2026-10-13T13:00:00.000Z'})).status,'reused');
  const directory = path.join(input.vaultRoot,'.temp/daily-tasks');
  assert.deepEqual((await readdir(directory)).filter(name => name.endsWith('.tmp')),[]);
});
