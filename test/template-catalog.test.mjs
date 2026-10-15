import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { templateKinds, templateFingerprint, loadTemplateCatalog, identifyTemplate, compareTemplates } from '#core/templates/catalog.mjs';

test('template fingerprints normalize line endings while preserving formatting differences', () => {
  const lf = '# Plan\n\nWork  \n';
  assert.equal(templateFingerprint(lf), `sha256:${createHash('sha256').update(lf).digest('hex')}`);
  assert.equal(templateFingerprint(lf.replaceAll('\n', '\r\n')), templateFingerprint(lf));
  assert.notEqual(templateFingerprint(lf.replace('  \n', '\n')), templateFingerprint(lf));
  assert.notEqual(templateFingerprint(lf.trimEnd()), templateFingerprint(lf));
});

test('bundled catalog loads all template kinds relative to the module instead of the process directory', async () => {
  const catalog = await loadTemplateCatalog();
  assert.deepEqual(templateKinds, ['dailyPlan', 'planDayReview', 'projectIndex', 'milestone', 'task']);
  assert.deepEqual(Object.keys(catalog), templateKinds);
  const contracts = ['daily-plan-v1', 'review-v1', 'project-v1', 'milestone-v2', 'task-v2'];
  for (const [index, kind] of templateKinds.entries()) {
    assert.equal(catalog[kind].kind, kind);
    assert.equal(catalog[kind].source, 'bundled');
    assert.equal(catalog[kind].contract, contracts[index]);
    assert.equal(catalog[kind].revision, templateFingerprint(await readFile(catalog[kind].path, 'utf8')));
    assert.equal(identifyTemplate(kind, catalog[kind].content, catalog).source, 'bundled');
  }
  const moduleUrl = new URL('../src/core/templates/catalog.mjs', import.meta.url).href;
  const elsewhere = execFileSync(process.execPath, ['--input-type=module', '-e', `import { loadTemplateCatalog } from ${JSON.stringify(moduleUrl)}; process.stdout.write(JSON.stringify(Object.keys(await loadTemplateCatalog())));`], {
    cwd: fileURLToPath(new URL('../skills/', import.meta.url)), encoding: 'utf8'
  });
  assert.deepEqual(JSON.parse(elsewhere), templateKinds);
});

test('verified retained history recognizes old bundled copies independently of a plugin checkout', async () => {
  const history = JSON.parse(await readFile(new URL('../src/core/templates/history.json', import.meta.url), 'utf8'));
  const catalog = await loadTemplateCatalog();
  assert.equal(history.schemaVersion, 1);
  for (const kind of templateKinds) {
    assert.ok(history.templates[kind].length > 0, `${kind} retains released content`);
    for (const entry of history.templates[kind]) {
      const expected = `sha256:${createHash('sha256').update(entry.content.replaceAll('\r\n', '\n')).digest('hex')}`;
      assert.equal(entry.revision, expected);
      assert.match(entry.provenance.commit, /^[a-f0-9]{40}$/);
      assert.match(entry.provenance.release, /^\d+\.\d+\.\d+$/);
      assert.match(entry.provenance.path, /^skills\/daily-tasks\/assets\/[^/]+\.md$/);
      const identified = identifyTemplate(kind, entry.content.replaceAll('\n', '\r\n'), catalog);
      assert.equal(identified.recognized, true);
      assert.equal(identified.revision, entry.revision);
      assert.equal(identified.contract, entry.contract);
      assert.equal(identified.source, entry.revision === catalog[kind].revision ? 'bundled' : 'bundled-copy');
    }
  }
  const oldPlan = catalog.dailyPlan.history.find(entry => entry.provenance.release === '0.2.0');
  assert.match(oldPlan.content, /- \*\*Next action:\*\*/);
  assert.equal(oldPlan.provenance.commit, '8bdeeacd44bda8179fafe0d96f0784f2aab82249');
  assert.equal(oldPlan.contract, 'daily-plan-v1');
  for (const kind of ['milestone', 'task']) {
    const oldRecord = catalog[kind].history.find(entry => entry.contract === `${kind}-v1`);
    assert.ok(oldRecord);
    assert.equal(identifyTemplate(kind, oldRecord.content, catalog).contract, `${kind}-v1`);
    assert.notEqual(oldRecord.contract, catalog[kind].contract);
  }
});

test('modified custom templates and unverified catalog revisions never become known copies', async () => {
  const catalog = await loadTemplateCatalog();
  const oldPlan = catalog.dailyPlan.history.find(entry => entry.provenance.release === '0.2.0');
  const content = oldPlan.content.replace('## Focus', '## My own focus');
  assert.deepEqual(identifyTemplate('dailyPlan', content, catalog), {
    kind: 'dailyPlan', source: 'custom', recognized: false,
    revision: templateFingerprint(content), contract: null
  });
  const invalidCurrent = {...catalog, dailyPlan: {...catalog.dailyPlan, revision: templateFingerprint(content)}};
  assert.throws(() => identifyTemplate('dailyPlan', content, invalidCurrent), /fingerprint/i);
  const invalidHistory = {...catalog, dailyPlan: {...catalog.dailyPlan, history: [{...oldPlan, revision: templateFingerprint(content)}]}};
  assert.throws(() => identifyTemplate('dailyPlan', content, invalidHistory), /fingerprint/i);
});

test('template comparison explains checklist-to-table layout, headings and new columns', async () => {
  const catalog = await loadTemplateCatalog();
  const oldPlan = catalog.dailyPlan.history.find(entry => entry.provenance.release === '0.2.0');
  const comparison = compareTemplates(oldPlan.content, catalog.dailyPlan.content);
  assert.equal(comparison.changed, true);
  assert.ok(comparison.headings.added.includes('## Selected for today'));
  assert.ok(comparison.headings.removed.includes('## Decisions to resolve'));
  assert.ok(comparison.tables.added.some(columns => columns.join(', ') === '#, Status, Project, Milestone, Task, Due Date'));
  assert.deepEqual(comparison.layout, {before: 'checklists', after: 'tables'});
  assert.ok(comparison.summary.some(line => /checklists.*tables/.test(line)));
  assert.ok(comparison.summary.some(line => /Milestone.*Due Date/.test(line)));
});

test('template comparison ignores instructional examples and reports exact unchanged content', () => {
  const before = '# Plan\n\n| Task | Due Date |\n| --- | --- |\n| Link | — |\n';
  const after = '# Plan\n\n| Task | Milestone | Due Date |\n| --- | --- | --- |\n| Link | Label | — |\n<!--\n## Hidden instructions\n| Internal | Columns |\n| --- | --- |\n-->\n';
  const comparison = compareTemplates(before, after);
  assert.deepEqual(comparison.headings, {added: [], removed: []});
  assert.deepEqual(comparison.tables, {added: [['Task', 'Milestone', 'Due Date']], removed: [['Task', 'Due Date']]});
  assert.deepEqual(comparison.columns, {added: ['Milestone'], removed: []});
  assert.ok(comparison.summary.includes('Added table columns: Milestone.'));
  const unchanged = compareTemplates(before, before.replaceAll('\n', '\r\n'));
  assert.equal(unchanged.changed, false);
  assert.deepEqual(unchanged.summary, ['No template changes.']);
});
