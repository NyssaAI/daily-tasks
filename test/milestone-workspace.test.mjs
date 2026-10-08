import test from 'node:test';
import assert from 'node:assert/strict';
import { parseRecord, validateRecords, checkClosure, checkLinks, recordMarkdownIsManaged } from '../lib/records/records.mjs';
import { reopenAncestors } from '../lib/reconciliation/reconciliation.mjs';
import { mkdir, mkdtemp, writeFile, readFile, rename } from 'node:fs/promises';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { projectInventory } from '../lib/inventory/inventory.mjs';

const id = n => `019a1234-5678-7abc-8def-${String(n).padStart(12,'0')}`;
const doc = (n,type,body,extra='') => `---\nid: ${id(n)}\ntype: ${type}\nrecord_version: 2\ntitle: Example\nowner: owner@example.test\n${type}-state: completed\ncreated_at: 2026-10-08T12:00:00Z\nupdated_at: 2026-10-08T12:00:00Z\n${extra}---\n# Example\n${body}`;
const criterion = (n,checked=true) => `- [${checked ? 'x' : ' '}] Observable result <!-- id: ${id(n)} -->`;
function graph() {
  return [parseRecord(doc(1,'project',''),'/p/project-index.md'),
    parseRecord(doc(2,'milestone',`## Definition of Done\n${criterion(4)}`,`project_id: ${id(1)}\n`),'/p/m1-example/m1-example.md'),
    parseRecord(doc(3,'task',`## Requirements\nDeliver a report.\n## Definition of Done\n${criterion(5)}`,`project_id: ${id(1)}\nmilestone_id: ${id(2)}\n`),'/p/m1-example/t1-report.md')];
}

test('embedded criteria stay distinct from navigation and allow evidence links and nested headings', () => {
  const text = doc(2,'milestone',`## Definition of Done\n### Delivery\n- [x] Read [[outputs/report.md|report]]\n  <!-- id: ${id(4)} -->\n\n\`\`\`md\n${criterion(99)}\n\`\`\`\n## Tasks\n- [x] [[t1-report|Report]] <!-- ref: ${id(3)} -->`, `project_id: ${id(1)}\n`);
  const record = parseRecord(text,'/p/m1-example/m1-example.md');
  assert.deepEqual(record.parse_errors,[]);
  assert.deepEqual(record.criteria.map(c => c.id),[id(4)]);
  assert.deepEqual(record.projections.map(c => c.id),[id(3)]);
  assert.deepEqual(record.refs.map(r => r.id),[id(3)]);
});

test('task and milestone closure require their own criteria, while legacy task closure stays readable', () => {
  const records = graph();
  assert.deepEqual(validateRecords(records),[]);
  for (const n of [1,2,3]) assert.equal(checkClosure(id(n),records).allowed,true);
  records[2].criteria[0].checked = false;
  for (const n of [1,2,3]) assert.equal(checkClosure(id(n),records).allowed,false);
  records[2].state = 'cancelled';
  assert.equal(checkClosure(id(2),records).allowed,true);
  records[1].criteria[0].checked = false;
  assert.equal(checkClosure(id(2),records).allowed,false);
  const legacy = parseRecord(doc(3,'task','',`project_id: ${id(1)}\nmilestone_id: ${id(2)}\n`).replace('record_version: 2\n',''),'/p/legacy.md');
  assert.equal(checkClosure(id(3),[records[0],records[1],legacy]).allowed,true);
});

test('new tasks missing DoD or containing duplicate criterion IDs cannot complete', () => {
  for (const body of ['', '## Definition of Done\n',`## Definition of Done\n${criterion(5)}\n${criterion(5)}`]) {
    const records = graph();
    records[2] = parseRecord(doc(3,'task',body,`project_id: ${id(1)}\nmilestone_id: ${id(2)}\n`),'/p/m1-example/t1-report.md');
    assert.equal(checkClosure(id(3),records).allowed,false);
  }
});

test('unchecking task DoD reopens that task and parents but milestone DoD leaves completed children alone', () => {
  const records = graph();
  records.forEach(r => r.resolved_at = '2026-10-08T12:00:00Z');
  records[2].criteria[0].checked = false;
  const result = reopenAncestors(records,[id(3)]);
  assert.deepEqual(new Set(result.changedIds),new Set([id(1),id(2),id(3)]));
  assert.equal(result.records[2].state,'not-started');
  assert.ok(result.records.every(r => r.resolved_at === undefined));
  assert.equal(records[2].state,'completed');
  const milestoneRecords = graph();
  milestoneRecords[1].criteria[0].checked = false;
  const reopened = reopenAncestors(milestoneRecords,[id(2)]);
  assert.equal(reopened.records[1].state,'in-progress');
  assert.equal(reopened.records[2].state,'completed');
});

test('numbered records remain discoverable with broken metadata and duplicate numbers are reported', () => {
  assert.equal(recordMarkdownIsManaged('# Missing metadata','/p/m1-example/t1-report.md'),true);
  const records = graph();
  records.push({...records[2],id:id(7),path:'/p/m1-example/t1-other.md',criteria:[{id:id(8),text:'Other',checked:true}]});
  assert.ok(validateRecords(records).some(d => d.code === 'invalid-number'));
});

test('legacy milestone conversion preserves criterion references and rejects competing DoD sources', () => {
  const records = graph();
  const legacy = parseRecord(doc(9,'dod',`## Definition of Done\n${criterion(4)}`,`project_id: ${id(1)}\nmilestone_id: ${id(2)}\n`).replace('record_version: 2\n',''),'/p/m1-example/definition-of-done.md');
  assert.equal(checkClosure(id(2),[...records,legacy]).allowed,false);
  const projection = {...records[0],refs:[{id:id(4),target:'m1-example/definition-of-done#Definition of Done'}]};
  const repair = checkLinks([projection,...records.slice(1)]).find(d => d.code === 'path-mismatch');
  assert.equal(repair.proposedTarget,'m1-example/m1-example#Definition of Done');
  projection.refs[0].target = repair.proposedTarget;
  assert.deepEqual(checkLinks([projection,...records.slice(1)]),[]);
});

test('criterion section boundaries reject malformed criteria without mistaking unrelated checkboxes for DoD', () => {
  for (const content of [`- [>] Unfinished <!-- id: ${id(5)} -->`, `- [x] Missing ID`,
    `| [ ] Table criterion |`,`${criterion(5)}\n## Definition of Done\n${criterion(6)}`]) {
    const records = graph();
    records[2] = parseRecord(doc(3,'task',`## Definition of Done\n${content}`,`project_id: ${id(1)}\nmilestone_id: ${id(2)}\n`));
    assert.equal(checkClosure(id(3),records).allowed,false);
  }
  const record = parseRecord(doc(3,'task',`## Requirements\n- [ ] Candidate\n## Definition of Done\n${criterion(5)}\n## Notes\n- [ ] Another candidate`));
  assert.equal(record.criteria.length,1);
  assert.equal(record.projections.length,2);
});

test('flat holding folders cannot introduce phantom tasks in either inventory or CLI inspection', async () => {
  await mkdir('.temp',{recursive:true});
  const vaultRoot = await mkdtemp(path.resolve('.temp/milestone-workspace-'));
  const projectsRoot = path.join(vaultRoot,'projects'), project = path.join(projectsRoot,'example');
  const milestone = path.join(project,'m1-example');
  const dailyPlansRoot = path.join(vaultRoot,'plans');
  for (const dir of [milestone,dailyPlansRoot,path.join(milestone,'inputs'),path.join(milestone,'outputs')]) await mkdir(dir,{recursive:true});
  const projectText = doc(1,'project',`- [x] [[m1-example/m1-example|Example]] <!-- ref: ${id(2)} -->`);
  const milestoneText = doc(2,'milestone',`## Definition of Done\n${criterion(4)}\n## Tasks\n- [ ] [[t1-report|Report]] <!-- ref: ${id(3)} -->`,`project_id: ${id(1)}\n`);
  const taskText = doc(3,'task',`## Requirements\nWrite the report.\n## Definition of Done\n${criterion(5)}\n## Inputs\n[[inputs/source.md]]\n## Outputs\n[[outputs/report.md]]`,`project_id: ${id(1)}\nmilestone_id: ${id(2)}\n`).replace('task-state: completed','task-state: not-started');
  await writeFile(path.join(project,'project-index.md'),projectText);
  await writeFile(path.join(milestone,'m1-example.md'),milestoneText);
  await writeFile(path.join(milestone,'t1-report.md'),taskText);
  // Imported task-shaped files must remain attachments even with live-looking IDs.
  await writeFile(path.join(milestone,'inputs/source.md'),taskText);
  await writeFile(path.join(milestone,'outputs/report.md'),taskText);
  const inventoryInput = {vaultRoot,projectsRoot,dailyPlansRoot,timezone:'America/Chicago',now:'2026-10-08T12:00:00Z'};
  const first = await projectInventory(inventoryInput);
  assert.deepEqual(first.inventory.tasks.map(t => t.id),[id(3)]);
  assert.deepEqual(first.inventory.diagnostics,[]);
  const inputPath = path.join(vaultRoot,'inspection.json');
  await writeFile(inputPath,JSON.stringify({projectsRoot}));
  const scan = spawnSync(process.execPath,[path.resolve('bin/daily-tasks.mjs'),'inspect-records','--input',inputPath],{cwd:vaultRoot,encoding:'utf8'});
  assert.equal(scan.status,0,scan.stderr);
  const inspected = JSON.parse(scan.stdout);
  assert.equal(inspected.records.length,3);
  assert.deepEqual(inspected.diagnostics,[]);
  await rename(path.join(milestone,'outputs/report.md'),path.join(milestone,'outputs/reviewed-report.md'));
  const revised = taskText.replace('outputs/report.md','outputs/reviewed-report.md');
  await writeFile(path.join(milestone,'t1-report.md'),revised);
  assert.equal((await projectInventory(inventoryInput)).status,'rebuilt');
  assert.equal(await readFile(path.join(milestone,'inputs/source.md'),'utf8'),taskText);
});
