import { mkdir, mkdtemp, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { isDeepStrictEqual } from 'node:util';
import { uuid7, isUuid7 } from '../lib/identity/identity.mjs';
import { localDay } from '../lib/time/time.mjs';
import { parseRecord } from '../lib/records/records.mjs';
import { parseViewRows } from '../lib/records/views.mjs';
import { inventory } from './inventory.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const hash = content => createHash('sha256').update(content).digest('hex');
const json = value => JSON.stringify(value, null, 2) + '\n';
const artifacts = ['declinedPlan', 'existingAfterAcceptance', 'acceptedPlan', 'reformattedPlan', 'chatReview'];
const requiredChoices = {
  decline: 'Keep the current daily-plan layout for this revision.',
  accept: 'Use the new daily-plan layout for new documents only.',
  reformat: 'Also reformat today’s existing plan using the new daily-plan layout.',
  review: 'Keep my compact chat-review template unchanged.',
};

/** Seed a synthetic starting vault only; never generate successful host outcomes. */
export async function seedTemplateUpdateFixture(parent, now = new Date().toISOString()) {
  const scratchRoot = path.join(root, '.temp');
  const relative = path.relative(scratchRoot, path.resolve(parent));
  if (!relative || relative === '..' || relative.startsWith('..' + path.sep) || path.isAbsolute(relative)) {
    throw new TypeError('Choose a fixture parent below this repository’s .temp directory');
  }
  const history = JSON.parse(await readFile(path.join(root, 'lib/templates/history.json'), 'utf8'));
  const legacy = history.templates.dailyPlan.find(entry => entry.provenance.release === '0.2.0');
  if (!legacy?.content || !legacy.content.includes('**Next action:**')) throw new Error('Verified historical checklist template unavailable');
  await mkdir(parent, {recursive: true});
  const directory = await mkdtemp(path.join(path.resolve(parent), 'host-'));
  const vaultRoot = path.join(directory, 'vault');
  const stateRoot = path.join(vaultRoot, '.nyssa-ai/daily-tasks');
  const projectsRoot = path.join(vaultRoot, '1-projects');
  const dailyPlansRoot = path.join(vaultRoot, '2-areas/daily-plans');
  const project = path.join(projectsRoot, '2026.01.01-fixture');
  const evidenceRoot = path.join(directory, 'evidence');
  for (const folder of [path.join(project, 'm1-first'), dailyPlansRoot, path.join(stateRoot, 'templates'), evidenceRoot]) await mkdir(folder, {recursive: true});
  const ids = Object.fromEntries(['project', 'milestone', 'carry', 'done', 'cancelled', 'delegated', 'unresolved', 'newTask', 'today', 'future', 'history'].map(key => [key, uuid7()]));
  const timezone = 'America/Chicago', userEmail = 'fixture@example.test';
  const today = localDay(now, timezone);
  const shift = amount => localDay(new Date(Date.parse(today.replaceAll('.', '-') + 'T12:00:00Z') + amount * 86400000).toISOString(), timezone);
  const future = shift(1), previous = shift(-1);
  const created = '2026-10-08T16:00:00.000Z';
  const taskRows = [
    {id: ids.carry, mark: '>', target: '../../1-projects/2026.01.01-fixture/m1-first/t1-carry', label: 'Carry task', carried: true},
    {id: ids.done, mark: 'x', target: '../../1-projects/2026.01.01-fixture/m1-first/t2-done', label: 'Finished task', carried: false},
    {id: ids.cancelled, mark: '-', target: '../../1-projects/2026.01.01-fixture/m1-first/t3-cancelled', label: 'Cancelled task', carried: false},
    {id: ids.unresolved, mark: ' ', target: '../../1-projects/2026.01.01-fixture/m1-first/t99-missing', label: 'Missing reference', carried: false},
    {id: ids.delegated, mark: ' ', target: '../../1-projects/2026.01.01-fixture/m1-first/t4-delegated', label: 'Delegated task', carried: false},
  ];
  const newRow = {id: ids.newTask, mark: ' ', target: '../../1-projects/2026.01.01-fixture/m1-first/t5-new', label: 'New task', carried: false};
  const record = (id, type, title, state, body, extra = '') => `---\nid: ${id}\ntype: ${type}\n${['task', 'milestone'].includes(type) ? 'record_version: 2\n' : ''}title: "${title}"\nowner: ${userEmail}\n${type}-state: ${state}\ncreated_at: "${created}"\nupdated_at: "${now}"\n${extra}---\n# ${title}\n\n${body}\n`;
  const canonicalFiles = [];
  for (const row of [...taskRows.filter(row => row.id !== ids.unresolved), newRow]) {
    const filename = path.resolve(dailyPlansRoot, row.target + '.md');
    const state = ({'>': 'in-progress', 'x': 'completed', '-': 'cancelled'})[row.mark] ?? 'not-started';
    const body = `## Definition of Done\n\n- [${row.mark === 'x' ? 'x' : ' '}] Deliver the named fixture outcome. <!-- id: ${uuid7()} -->\n\n## Notes\n\nSynthetic record; no external actions.\n`;
    const lifecycle = ['completed', 'cancelled'].includes(state) ? `resolved_at: "${now}"\n` : state === 'in-progress' ? `started_at: "${now}"\n` : '';
    await writeFile(filename, record(row.id, 'task', row.label, state, body, `project_id: ${ids.project}\nmilestone_id: ${ids.milestone}\n${row.id === ids.delegated ? 'assignee: colleague@example.test\n' : ''}${lifecycle}`));
    canonicalFiles.push(filename);
  }
  const projectIndex = path.join(project, 'project-index.md');
  const milestone = path.join(project, 'm1-first/m1-first.md');
  await writeFile(projectIndex, record(ids.project, 'project', 'Fixture', 'in-progress', `## Milestones\n\n- [>] [[m1-first/m1-first|First]] <!-- ref: ${ids.milestone} -->\n`));
  await writeFile(milestone, record(ids.milestone, 'milestone', 'First', 'in-progress', `## Tasks\n\n${[...taskRows.filter(row => row.id !== ids.unresolved), newRow].map(row => `- [${row.mark}] [[${path.basename(row.target)}|${row.label}]] <!-- ref: ${row.id} -->`).join('\n')}\n\n## Definition of Done\n\n- [ ] Review all fixture outcomes. <!-- id: ${uuid7()} -->`, `project_id: ${ids.project}\nstarted_at: "${now}"\n`));
  canonicalFiles.push(projectIndex, milestone);
  const carryReference = `<!-- carried-from: ${previous}; plan: ${ids.history}; task: ${ids.carry} -->`;
  const prose = ['Keep the supplier wording exactly.', 'Do not discard the unresolved reference.', carryReference];
  const rows = selected => selected.map(row => `- [${row.mark}] ${row.carried ? '↺ ' : ''}[[${row.target}|${row.label}]] <!-- ref: ${row.id} -->\n  - **Project:** Fixture\n`).join('\n');
  const plan = (date, id, selected) => `---\nid: ${id}\ntype: daily-plan\ntitle: "Daily plan ${date}"\ndocument-maturity: reviewed\ntimezone: "${timezone}"\ncreated_at: "${created}"\nupdated_at: "${now}"\n---\n# Daily plan — ${date}\n\n**Timezone:** ${timezone}\n\n## My work\n\n${rows(selected.filter(row => row.id !== ids.delegated))}\n## Delegated work\n\n${rows(selected.filter(row => row.id === ids.delegated))}\n## Notes\n\n${prose.join('\n\n')}\n`;
  const paths = {today: path.join(dailyPlansRoot, today + '-daily-plan.md'), future: path.join(dailyPlansRoot, future + '-daily-plan.md'), history: path.join(dailyPlansRoot, previous + '-daily-plan.md'), oldTemplate: path.join(stateRoot, 'templates/daily-plan.md'), customReview: path.join(stateRoot, 'templates/plan-day-select-tasks-screen.md')};
  for (const name of artifacts) paths[name] = path.join(evidenceRoot, name + '.md');
  const todayBefore = plan(today, ids.today, taskRows);
  await writeFile(paths.today, todayBefore);
  await writeFile(paths.history, plan(previous, ids.history, [taskRows[0]]));
  await writeFile(paths.oldTemplate, legacy.content);
  await writeFile(paths.customReview, '# My compact review\n\n## Chosen work\n\n- [ ] [[RELATIVE_TASK_PATH|TASK_TITLE]] <!-- ref: TASK_UUID -->\n\n## Other available work\n\n- [ ] [[RELATIVE_AVAILABLE_TASK_PATH|AVAILABLE_TASK_TITLE]] <!-- ref: AVAILABLE_TASK_UUID -->\n\nReply with an explicit action and task numbers.\n');
  await writeFile(path.join(stateRoot, 'profile.json'), json({schema_version: 1, user: {name: 'Fixture', email: userEmail}, timezone, priorities: [], vaultRoot: '.', projectsRoot: './1-projects', dailyPlansRelative: '2-areas/daily-plans', projectIndex: {ttlSeconds: 14400}, templates: {dailyPlan: paths.oldTemplate, planDayReview: paths.customReview}}));
  const unchangedFiles = Object.fromEntries(await Promise.all([...canonicalFiles, paths.history, paths.oldTemplate, paths.customReview].map(async filename => [filename, hash(await readFile(filename))])));
  const candidate = await inventory();
  const fixture = {schemaVersion: 1, directory, vaultRoot, projectsRoot, dailyPlansRoot, stateRoot, evidenceRoot, now, today, future, timezone, ids, paths,
    candidate: {hash: candidate.hash, skills: Object.fromEntries(Object.entries(candidate.files).filter(([name]) => /^skills\/daily-tasks(?:-plan)?\/SKILL\.md$/.test(name)))},
    templates: {oldRevision: legacy.revision, availableHash: hash((await readFile(path.join(root, 'skills/daily-tasks/assets/daily-plan.md'), 'utf8')).replaceAll('\r\n', '\n'))},
    requiredChoices, expected: {todayHash: hash(todayBefore), todayRows: taskRows, futureRows: [newRow], created, prose, unchangedFiles}};
  await writeFile(path.join(directory, 'fixture.json'), json(fixture));
  return fixture;
}

function selectedRows(markdown) {
  return parseViewRows(markdown).filter(row => row.mark !== undefined).map(row => ({id: row.id, mark: row.mark, target: row.target, carried: row.title.startsWith('↺ ')}));
}

function expectedRows(rows) {
  return rows.map(({id, mark, target, carried}) => ({id, mark, target, carried}));
}

function visibleMarkdown(markdown) {
  return markdown.replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n/, '').replace(/```[\s\S]*?```|~~~[\s\S]*?~~~/g, '').replace(/<!--[\s\S]*?-->/g, '');
}

function tableLayout(markdown) {
  const visible = visibleMarkdown(markdown);
  const rows = visible.split(/\r?\n/);
  const columns = line => line.trim().split(/(?<!\\)\|/).slice(1, -1).map(cell => cell.trim());
  let headers = 0, inTable = false;
  for (let index = 0; index < rows.length; index++) {
    const line = rows[index];
    if (!/^\s*\|/.test(line)) { inTable = false; continue; }
    if (/\|\s*#\s*\|/.test(line)) {
      if (!/^\|\s*#\s*\|\s*Status\s*\|\s*Project\s*\|\s*Milestone\s*\|\s*Task\s*\|\s*Due Date\s*\|\s*$/.test(line)) return false;
      const delimiter = rows[index + 1] ?? '';
      const cells = columns(delimiter);
      if (!/^\s*\|.*\|\s*$/.test(delimiter) || cells.length !== 6 || !cells.every(cell => /^:?-+:?$/.test(cell))) return false;
      headers++; inTable = true; index++;
    } else if (/\[[ x>\-]\]/.test(line) && (!inTable || columns(line).length !== 6 || !/\|\s*$/.test(line))) return false;
  }
  return headers > 0 &&
    !/^\s*[-*]\s+\[[ x>\-]\].*\[\[/m.test(visible) &&
    /^### My work\s*$/m.test(visible) && /^### Delegated work\s*$/m.test(visible) &&
    /^#### Fixture \/ First\s*$/m.test(visible) &&
    /^Open projects:\s*\d+\s+Open tasks:\s*\d+\s+Late tasks:\s*\d+\s*$/m.test(visible) &&
    /^Legend: .*\[>\].*\[x\].*\[-\].*↺/m.test(visible);
}

async function optionalRead(filename) {
  try { return await readFile(filename, 'utf8'); }
  catch (error) { if (error.code === 'ENOENT') return undefined; throw error; }
}

/** Inspect actual saved artifacts; reported native success also requires a captured host receipt. */
export async function inspectTemplateUpdateEvidence(fixture, receipt) {
  if (fixture.schemaVersion !== 1) throw new Error('Unsupported template-update fixture revision');
  const texts = Object.fromEntries(await Promise.all(artifacts.map(async name => [name, await optionalRead(fixture.paths[name])])));
  const missingArtifacts = artifacts.filter(name => texts[name] === undefined);
  const checks = [];
  const check = (id, passed) => checks.push({id, passed: !!passed});
  check('declined-layout', texts.declinedPlan !== undefined && hash(texts.declinedPlan) === fixture.expected.todayHash);
  check('existing-after-acceptance', texts.existingAfterAcceptance !== undefined && hash(texts.existingAfterAcceptance) === fixture.expected.todayHash);
  check('accepted-layout', tableLayout(texts.acceptedPlan ?? ''));
  check('accepted-rows', isDeepStrictEqual(selectedRows(texts.acceptedPlan ?? ''), expectedRows(fixture.expected.futureRows)));
  const future = parseRecord(texts.acceptedPlan ?? '', fixture.paths.future);
  check('accepted-identity', !future.parse_errors.length && future.type === 'daily-plan' && isUuid7(future.id) && future.id !== fixture.ids.today && future.id !== fixture.ids.history && future.title?.includes(fixture.future) && Number.isFinite(Date.parse(future.created_at)));
  const formatted = texts.reformattedPlan ?? '';
  check('reformatted-layout', tableLayout(formatted));
  check('reformatted-rows', isDeepStrictEqual(selectedRows(formatted), expectedRows(fixture.expected.todayRows)));
  const record = parseRecord(formatted, fixture.paths.today);
  check('reformatted-identity', !record.parse_errors.length && record.type === 'daily-plan' && record.id === fixture.ids.today && record.created_at === fixture.expected.created && record.title?.includes(fixture.today));
  check('reformatted-prose', fixture.expected.prose.every(prose => formatted.includes(prose)) && formatted.includes(fixture.timezone));
  const delegated = formatted.split(/^### Delegated work\s*$/m)[1]?.split(/^## /m)[0] ?? '';
  check('reformatted-responsibility', isDeepStrictEqual(selectedRows(delegated), expectedRows(fixture.expected.todayRows.filter(row => row.id === fixture.ids.delegated))));
  const review = visibleMarkdown(texts.chatReview ?? '');
  check('independent-review', /^#{1,2} My compact review\s*$/m.test(review) && /^#{2,3} Chosen work\s*$/m.test(review) && /^#{2,3} Other available work\s*$/m.test(review) &&
    /^- \[[ x>\-]\] /m.test(review) && !/^\s*\|/m.test(review) && review.includes('Reply with an explicit action and task numbers.'));
  const alteredFiles = [];
  for (const [filename, expected] of Object.entries(fixture.expected.unchangedFiles)) {
    const actual = await optionalRead(filename);
    if (actual === undefined || hash(actual) !== expected) alteredFiles.push(filename);
  }
  check('preserved-source-files', !alteredFiles.length);
  const native = await inspectNativeReceipt(fixture, receipt, texts);
  const artifactsValid = checks.every(item => item.passed);
  return {status: native.valid ? artifactsValid ? 'pass' : 'fail' : 'unverified', artifactsValid, nativeEvidenceValid: native.valid,
    checks, missingArtifacts, alteredFiles, nativeIssues: native.issues,
    limitation: 'File verification checks captured evidence. A reviewer must confirm invocation/discovery/transcript exports came from the actual isolated host; fixture or verifier tests do not establish host activation.'};
}

async function inspectNativeReceipt(fixture, receipt, texts) {
  const issues = [];
  if (!receipt || receipt.execution !== 'native-host') return {valid: false, issues: ['No native-host invocation receipt; synthetic/direct CLI results are unverified.']};
  if (receipt.schemaVersion !== 1 || !['name', 'version', 'model', 'sessionId'].every(key => typeof receipt.host?.[key] === 'string' && receipt.host[key].trim())) issues.push('Host identity, version, model and session ID required.');
  if (receipt.isolated !== true || receipt.candidateHash !== fixture.candidate.hash) issues.push('Receipt must identify the isolated fixture and exact candidate.');
  if ((await inventory()).hash !== fixture.candidate.hash) issues.push('Candidate changed after fixture creation; reseed after source freeze.');
  const readEvidence = async (item, name) => {
    if (!item || typeof item.path !== 'string' || !path.isAbsolute(item.path) || !/^[a-f0-9]{64}$/.test(item.sha256 ?? '')) { issues.push(`${name} evidence path/hash required.`); return ''; }
    const text = await optionalRead(item.path);
    if (!text || hash(text) !== item.sha256) { issues.push(`${name} evidence missing or changed.`); return ''; }
    return text;
  };
  const invocation = await readEvidence(receipt.invocation, 'Invocation');
  const discovery = await readEvidence(receipt.discovery, 'Discovery');
  const transcript = await readEvidence(receipt.transcript, 'Transcript');
  if (!invocation.includes(receipt.host?.sessionId ?? '\0') || !invocation.includes(receipt.host?.name ?? '\0')) issues.push('Invocation must contain the actual host and session identity.');
  for (const [source, expectedHash] of Object.entries(fixture.candidate.skills)) {
    const skill = receipt.loadedSkills?.find(item => item.source === source);
    if (!skill || !path.isAbsolute(skill.path ?? '') || !discovery.includes(skill.path)) { issues.push(`Missing discovered candidate skill: ${source}`); continue; }
    const content = await optionalRead(skill.path);
    if (!content || hash(content.replaceAll('\r\n', '\n')) !== expectedHash || skill.sha256 !== expectedHash) issues.push(`Loaded skill differs from candidate: ${source}`);
  }
  let messages = [];
  try { messages = JSON.parse(transcript).messages; if (!Array.isArray(messages)) messages = []; }
  catch { issues.push('Transcript must export original role/content messages as JSON.'); }
  let priorChoice = -1;
  for (const choice of ['decline', 'accept', 'reformat']) {
    const position = messages.findIndex((message, index) => index > priorChoice && message.role === 'user' && typeof message.content === 'string' && message.content.includes(requiredChoices[choice]));
    if (position < 0) issues.push(`Transcript lacks explicit user ${choice} choice in scenario order.`);
    else priorChoice = position;
  }
  if (!messages.some(message => message.role === 'user' && typeof message.content === 'string' && message.content.includes(requiredChoices.review))) issues.push('Transcript lacks independent user review-template choice.');
  if (!messages.some(message => message.role === 'assistant' && message.content === texts.chatReview)) issues.push('Captured review is not an actual assistant message in the transcript.');
  for (const name of artifacts) if (!texts[name] || receipt.outputs?.[name]?.path !== fixture.paths[name] || receipt.outputs[name].sha256 !== hash(texts[name])) issues.push(`Missing or changed captured output: ${name}`);
  for (const [live, capture] of [['today', 'reformattedPlan'], ['future', 'acceptedPlan']]) if (await optionalRead(fixture.paths[live]) !== texts[capture]) issues.push(`Saved ${live} document does not match its final captured output.`);
  return {valid: !issues.length, issues};
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const mode = process.argv[2];
  if (mode === 'seed') {
    const fixture = await seedTemplateUpdateFixture(process.argv[3] ?? path.join(root, '.temp/template-update-host'));
    console.log(json({fixture: path.join(fixture.directory, 'fixture.json'), vaultRoot: fixture.vaultRoot, date: fixture.today, status: 'unverified'}));
  } else if (mode === 'verify') {
    const fixture = JSON.parse(await readFile(process.argv[3], 'utf8'));
    const receipt = process.argv[4] ? JSON.parse(await readFile(process.argv[4], 'utf8')) : undefined;
    const result = await inspectTemplateUpdateEvidence(fixture, receipt);
    console.log(json(result));
    if (result.status !== 'pass') process.exitCode = 1;
  } else throw new Error('Use template-updates.mjs seed [ABSOLUTE_REPO_TEMP_DIR] or verify ABSOLUTE_FIXTURE_JSON [ABSOLUTE_NATIVE_RECEIPT_JSON]');
}
