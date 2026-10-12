import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { seedTemplateUpdateFixture, inspectTemplateUpdateEvidence } from '../evals/template-updates.mjs';

const scratch = path.resolve('.temp/template-evaluation');

// Calibration artifacts are authored by test code, never a native host invocation.
async function calibratedFixture() {
  const fixture = await seedTemplateUpdateFixture(scratch, '2026-10-12T16:00:00.000Z');
  const before = await readFile(fixture.paths.today, 'utf8');
  const table = (text, rows) => text
    .replace('## My work', '## Selected for today\n\n### My work\n\n#### Fixture / First')
    .replace('## Delegated work', '### Delegated work\n\n#### Fixture / First')
    .replace(/- \[([ x>\-])\] (.+)\n  - \*\*Project:\*\* Fixture\n/g, (_, mark, body) =>
      `| ${rows.indexOf(body.match(/ref: ([^ ]+)/)?.[1]) + 1} | [${mark}] | Fixture | First | ${body.replaceAll('|', '\\|')} | — |\n`)
    .replace(/((?:\| \d+[^\n]*\n)+)/g, '| # | Status | Project | Milestone | Task | Due Date |\n| --- | --- | --- | --- | --- | --- |\n$1')
    .replace('## Notes', 'Legend: [ ] not started · [>] in progress · [x] completed · [-] cancelled · ↺ carried forward\n\n## Notes and references')
    .replace('**Timezone:**', 'Open projects: 1          Open tasks: 3          Late tasks: 0\n\n**Timezone:**');
  await writeFile(fixture.paths.declinedPlan, before);
  await writeFile(fixture.paths.existingAfterAcceptance, before);
  await writeFile(fixture.paths.reformattedPlan, table(before, fixture.expected.todayRows.map(row => row.id)));
  const future = before
    .replace(fixture.ids.today, fixture.ids.future)
    .replaceAll(fixture.today, fixture.future)
    .replace(/## My work[\s\S]*?## Notes/, `## My work\n\n- [ ] [[${fixture.expected.futureRows[0].target}|New task]] <!-- ref: ${fixture.ids.newTask} -->\n  - **Project:** Fixture\n\n## Delegated work\n\nNo delegated work.\n\n## Notes`);
  await writeFile(fixture.paths.acceptedPlan, table(future, [fixture.ids.newTask]));
  await writeFile(fixture.paths.chatReview, `## My compact review\n\n### Chosen work\n\n${fixture.expected.todayRows.map(row => `- [${row.mark}] [[${row.target}|Task]] <!-- ref: ${row.id} -->`).join('\n')}\n\n### Other available work\n\n- [ ] [[${fixture.expected.futureRows[0].target}|New task]] <!-- ref: ${fixture.ids.newTask} -->\n\nReply with an explicit action and task numbers.\n`);
  return fixture;
}

test('template evaluation seed remains unverified without actual saved host output', async () => {
  const fixture = await seedTemplateUpdateFixture(scratch, '2026-10-12T16:00:00.000Z');
  const result = await inspectTemplateUpdateEvidence(fixture);
  assert.equal(result.status, 'unverified');
  assert.equal(result.artifactsValid, false);
  assert.ok(result.missingArtifacts.includes('acceptedPlan'));
  assert.equal(result.nativeEvidenceValid, false);
});

test('template evaluation accepts correct artifact structure without promoting synthetic writes to host evidence', async () => {
  const fixture = await calibratedFixture();
  const result = await inspectTemplateUpdateEvidence(fixture);
  assert.equal(result.artifactsValid, true, JSON.stringify(result.checks));
  assert.equal(result.status, 'unverified');
  assert.equal(result.nativeEvidenceValid, false);
  const receipt = {execution: 'synthetic', status: 'pass'};
  assert.equal((await inspectTemplateUpdateEvidence(fixture, receipt)).status, 'unverified');
});

for (const [name, artifact, transform, check] of [
  ['checklist falsely labelled as adopted table', 'acceptedPlan', (_, fixture) => readFile(fixture.paths.today, 'utf8'), 'accepted-layout'],
  ['table with wrong columns', 'reformattedPlan', text => text.replaceAll('| Milestone |', '| Estimate |'), 'reformatted-layout'],
  ['pipe rows without table delimiters', 'acceptedPlan', text => text.replace(/^\| ---.*\n/gm, ''), 'accepted-layout'],
  ['task rows outside table blocks', 'reformattedPlan', text => text.replace(/(\| ---.*\n)/, '$1\n'), 'reformatted-layout'],
  ['completed task reopened', 'reformattedPlan', text => text.replace('[x]', '[ ]'), 'reformatted-rows'],
  ['cancelled task removed', 'reformattedPlan', text => text.replace(/^\| .*\[-\].*\n/m, ''), 'reformatted-rows'],
  ['carry marker removed', 'reformattedPlan', text => text.replace('↺ [[', '[['), 'reformatted-rows'],
  ['task link retargeted', 'reformattedPlan', text => text.replace('t1-carry', 't1-other'), 'reformatted-rows'],
  ['task order changed', 'reformattedPlan', text => {
    const lines = text.split('\n'), first = lines.findIndex(line => line.startsWith('| 1 |')), second = lines.findIndex(line => line.startsWith('| 2 |'));
    [lines[first], lines[second]] = [lines[second], lines[first]];
    return lines.join('\n');
  }, 'reformatted-rows'],
  ['creation timestamp changed', 'reformattedPlan', text => text.replace('created_at: "2026-10-08T16:00:00.000Z"', 'created_at: "2026-10-12T16:00:00.000Z"'), 'reformatted-identity'],
  ['plan identity changed', 'reformattedPlan', (text, fixture) => text.replace(fixture.ids.today, fixture.ids.future), 'reformatted-identity'],
  ['new plan missing its identity', 'acceptedPlan', text => text.replace(/^id: .*\n/m, ''), 'accepted-identity'],
  ['unresolved reference dropped', 'reformattedPlan', text => text.replace(/^\| .*Missing reference.*\n/m, ''), 'reformatted-rows'],
  ['user notes dropped', 'reformattedPlan', text => text.replace('Keep the supplier wording exactly.', ''), 'reformatted-prose'],
  ['source provenance dropped', 'reformattedPlan', text => text.replace(/<!-- carried-from: .*? -->/, ''), 'reformatted-prose'],
  ['chat review incorrectly adopts saved-plan layout', 'chatReview', (_, fixture) => readFile(fixture.paths.reformattedPlan, 'utf8'), 'independent-review'],
  ['new revision rewrites existing plan without reformat approval', 'existingAfterAcceptance', (_, fixture) => readFile(fixture.paths.reformattedPlan, 'utf8'), 'existing-after-acceptance'],
  ['delegated work moved into personal work', 'reformattedPlan', text => text.replace('### Delegated work', '### Extra personal work'), 'reformatted-responsibility'],
]) test(`template evaluation rejects ${name}`, async () => {
  const fixture = await calibratedFixture();
  const file = fixture.paths[artifact];
  await writeFile(file, await transform(await readFile(file, 'utf8'), fixture));
  const result = await inspectTemplateUpdateEvidence(fixture);
  assert.equal(result.artifactsValid, false);
  assert.equal(result.checks.find(item => item.id === check)?.passed, false);
  assert.notEqual(result.status, 'pass');
});

test('template evaluation refuses a native label without invocation and discovery evidence', async () => {
  const fixture = await calibratedFixture();
  const result = await inspectTemplateUpdateEvidence(fixture, {execution: 'native-host', status: 'pass'});
  assert.equal(result.artifactsValid, true);
  assert.equal(result.status, 'unverified');
  assert.equal(result.nativeEvidenceValid, false);
});

test('template evaluation rejects historical plan edits and preserves the original custom source', async () => {
  for (const key of ['history', 'customReview', 'oldTemplate']) {
    const fixture = await calibratedFixture();
    await writeFile(fixture.paths[key], (await readFile(fixture.paths[key], 'utf8')) + '\nUnauthorized rewrite.\n');
    const result = await inspectTemplateUpdateEvidence(fixture);
    assert.equal(result.artifactsValid, false);
    assert.deepEqual(result.alteredFiles, [fixture.paths[key]]);
  }
});
