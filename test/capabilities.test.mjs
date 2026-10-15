import test, { after } from 'node:test';
import assert from 'node:assert/strict';
import { cp, mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import { validateProfile } from '#core/profile/profile.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
await mkdir(path.join(root, '.temp'), { recursive:true });
const fixture = await mkdtemp(path.join(root, '.temp/capabilities-test-'));
after(() => rm(fixture, { recursive:true, force:true }));
for (const name of ['scripts','skills','src','plugin.json','package.json']) {
  await cp(path.join(root,name),path.join(fixture,name),{recursive:true});
}
execFileSync(process.execPath,['scripts/write-capabilities.mjs'],{cwd:fixture});
const capabilities = JSON.parse(await readFile(path.join(fixture,'capabilities.json'),'utf8'));
const profileSchema = capabilities.operations.find(operation => operation.name === 'validate-profile').inputSchema;
const branches = () => {
  assert.equal(profileSchema.oneOf?.length,2,'profile inputs need separate v1 and partial v2 branches');
  return profileSchema.oneOf;
};
const fullProfile = {schema_version:1,user:{name:'Example',email:'example@example.test'},timezone:'UTC',
  priorities:['Work'],vaultRoot:root,projectsRoot:'./Projects',dailyPlansRelative:'Daily'};

test('generated profile contract accepts partial v2 and requires complete v1', () => {
  const [v1,v2] = branches();
  assert.equal(v1.properties.schema_version.const,1);
  assert.equal(v2.properties.schema_version.const,2);
  assert.deepEqual(v1.required,['schema_version','user','timezone','priorities','vaultRoot','projectsRoot','dailyPlansRelative']);
  assert.deepEqual(v2.required,['schema_version']);
  assert.equal(validateProfile(fullProfile).valid,true);
  assert.equal(validateProfile({schema_version:2,timezone:'UTC'}).valid,true);
  assert.equal(validateProfile({schema_version:2}).valid,true);
  for (const key of v1.required) {
    const incomplete = {...fullProfile}; delete incomplete[key];
    assert.equal(validateProfile(incomplete).valid,false,`v1 requires ${key}`);
  }
  for (const schema_version of [undefined,null,0,3,'2']) {
    assert.equal(validateProfile({...fullProfile,schema_version}).valid,false);
    assert.ok(![v1,v2].some(branch => branch.properties.schema_version.const === schema_version));
  }
});

test('profile branches describe nested leaves and v2 reset semantics', () => {
  const [v1,v2] = branches();
  const resets = {schema_version:2,timezone:null,priorities:null,templates:{task:null},projectIndex:{ttlSeconds:null}};
  assert.equal(validateProfile(resets).valid,true);
  for (const key of ['timezone','priorities']) {
    assert.ok(v2.properties[key].type.includes('null'));
    assert.ok(![].concat(v1.properties[key].type).includes('null'));
    assert.equal(validateProfile({...fullProfile,[key]:null}).valid,false);
  }
  for (const key of ['projectIndex','dailyPlan','milestone','task','planDayReview']) {
    assert.deepEqual(v2.properties.templates.properties[key].type,['string','null']);
    assert.equal(v1.properties.templates.properties[key].type,'string');
  }
  assert.deepEqual(v2.properties.projectIndex.properties.ttlSeconds.type,['integer','null']);
  assert.equal(v1.properties.projectIndex.properties.ttlSeconds.type,'integer');
  assert.equal(v2.additionalProperties,false);
  for (const key of ['user','templates','projectIndex']) assert.equal(v2.properties[key].additionalProperties,false);
  for (const key of ['user','vaultRoot','projectsRoot','dailyPlansRelative','templates','projectIndex']) {
    assert.ok(![].concat(v2.properties[key].type).includes('null'));
    assert.equal(validateProfile({schema_version:2,[key]:null}).valid,false);
  }
  assert.deepEqual(v1.properties.user.required,['name','email']);
  assert.equal(v2.properties.user.required,undefined);
  assert.deepEqual(v1.properties.projectIndex.required,['ttlSeconds']);
  assert.equal(v2.properties.projectIndex.required,undefined);
  assert.equal(validateProfile({schema_version:2,user:{email:'example@example.test'},templates:{},projectIndex:{}}).valid,true);
  assert.equal(validateProfile({schema_version:2,templates:{task:'~/task.MD'},projectIndex:{ttlSeconds:0}}).valid,true);
  assert.equal(validateProfile({schema_version:2,projectsRoot:'./Projects',dailyPlansRelative:'Daily'}).valid,true);
  for (const patch of [{other:'x'},{user:{name:null}},{user:{other:'x'}},{templates:{other:null}},{projectIndex:{other:1}},{projectIndex:{ttlSeconds:-1}},{projectIndex:{ttlSeconds:1.5}}]) {
    assert.equal(validateProfile({schema_version:2,...patch}).valid,false,JSON.stringify(patch));
  }
  const ttl = v2.properties.projectIndex.properties.ttlSeconds;
  assert.equal(ttl.minimum,0);
  assert.equal(ttl.maximum,Number.MAX_SAFE_INTEGER);
});

test('metadata supplies structural constraints and identifies runtime semantic checks', () => {
  const [,v2] = branches();
  for (const value of ['', '  ']) {
    assert.equal(new RegExp(v2.properties.user.properties.name.pattern).test(value),false);
    assert.equal(validateProfile({schema_version:2,user:{name:value}}).valid,false);
    assert.equal(new RegExp(v2.properties.priorities.items.pattern).test(value),false);
    assert.equal(validateProfile({schema_version:2,priorities:[value]}).valid,false);
  }
  for (const value of ['invalid','name@localhost','name @example.test']) {
    assert.equal(new RegExp(v2.properties.user.properties.email.pattern).test(value),false);
    assert.equal(validateProfile({schema_version:2,user:{email:value}}).valid,false);
  }
  assert.match(profileSchema.description,/runtime.*timezone/i);
  assert.match(profileSchema.description,/path/i);
  assert.match(profileSchema.description,/complete.*workspace/i);
  assert.equal(new RegExp(v2.properties.timezone.pattern).test('not-a-zone'),true,'a string shape cannot establish a valid timezone');
  assert.equal(validateProfile({schema_version:2,timezone:'not-a-zone'}).valid,false);
  assert.equal(validateProfile({schema_version:2,projectsRoot:'./../outside'}).valid,false);
  assert.equal(validateProfile({schema_version:2,dailyPlansRelative:'../outside'}).valid,false);
});

test('warm metadata exposes durable layered selectors and their exclusive legacy alternative', () => {
  const warm = capabilities.operations.find(operation => operation.name === 'warm-project-index');
  const schema = warm.inputSchema;
  assert.equal(schema.properties.stateRoot?.type,'string');
  assert.deepEqual(schema.not,{required:['profilePath','configurationSources']});
  const sources = schema.properties.configurationSources;
  assert.equal(sources.type,'object');
  assert.equal(sources.properties.schemaVersion.const,1);
  assert.deepEqual(sources.required,['schemaVersion','user','project']);
  assert.equal(sources.additionalProperties,false);
  for (const scope of ['user','project']) {
    assert.deepEqual(sources.properties[scope].required,['profilePath']);
    assert.deepEqual(sources.properties[scope].properties.profilePath.type,['string','null']);
    assert.equal(sources.properties[scope].additionalProperties,false);
  }
  assert.match(warm.invocation,/--configuration-sources JSON/);
  assert.match(warm.invocation,/--state-root ABSOLUTE_PATH/);
  for (const transient of ['preferenceOverrides','profile','now','today']) assert.equal(schema.properties[transient],undefined);
});

test('generated save-review contract retains required screen evidence without imposing it on rollover', () => {
  const schema = capabilities.operations.find(operation => operation.name === 'planning-state').inputSchema;
  const conditional = schema.allOf?.find(rule => rule.if?.properties?.action?.const === 'save-review');
  assert.ok(conditional,'save-review needs action-specific requirements');
  assert.deepEqual(conditional.if.required,['action']);
  assert.deepEqual(conditional.then.required,['expectedReviewHash','reviewMarkdown']);
  assert.deepEqual(conditional.then.properties.reviewMarkdown,{type:'string',minLength:1});
  assert.ok(!schema.required.includes('reviewMarkdown'));
  assert.ok(!schema.required.includes('expectedReviewHash'));
});

test('repository validation rejects missing or drifted versioned profile metadata', async () => {
  execFileSync(process.execPath,['scripts/validate.mjs'],{cwd:fixture});
  for (const mutate of [
    schema => { delete schema.oneOf; },
    schema => { schema.oneOf = [schema.oneOf[0]]; },
    schema => { schema.oneOf[1].required.push('user'); },
    schema => { schema.oneOf[0].required = schema.oneOf[0].required.filter(key => key !== 'dailyPlansRelative'); },
  ]) {
    const changed = structuredClone(capabilities);
    mutate(changed.operations.find(operation => operation.name === 'validate-profile').inputSchema);
    await writeFile(path.join(fixture,'capabilities.json'),JSON.stringify(changed));
    assert.throws(() => execFileSync(process.execPath,['scripts/validate.mjs'],{cwd:fixture,stdio:'pipe'}),
      error => /profile input contract/.test(error.stderr.toString()));
  }
});
