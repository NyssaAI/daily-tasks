import { readFile, readdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { root } from '../scripts/assemble.mjs';
import { inventory } from './inventory.mjs';
import { verifyResult, releaseReady } from './evidence.mjs';

const mode = process.argv[2];
if (!['write','check','release'].includes(mode)) throw new Error('Use report.mjs write|check|release');
const matrix = JSON.parse(await readFile(path.join(root,'evals/matrix.json'),'utf8'));
let runs = [];
try { runs = (await readdir(path.join(root,'evals/results'))).sort(); } catch (error) { if (error.code !== 'ENOENT') throw error; }
const candidate = await inventory();
const latest = new Map();
for (const runId of runs) {
  const directory = path.join(root,'evals/results',runId);
  const result = JSON.parse(await readFile(path.join(directory,'result.json'),'utf8'));
  if (result.runId !== runId) throw new Error(`Invalid run directory ${runId}`);
  // Earlier development receipts lack coordinates; retain without promoting them.
  if (!result.target) continue;
  const target = matrix.targets.find(item => item.id === result.target);
  await verifyResult(result,directory,target);
  const prior = latest.get(target.id);
  if (!prior || Date.parse(result.completed_at) > Date.parse(prior.completed_at)) latest.set(target.id,result);
}
let text = '# Latest evaluation\n\nDirect code and package checks are separate from native-host activation.\n\n';
text += '| Target / suite | Required | Platform / configuration | Result | Evidence / next check |\n| --- | --- | --- | --- | --- |\n';
for (const target of matrix.targets) {
  const value = latest.get(target.id);
  text += `| ${target.id} / ${target.suite} | ${target.required ? 'Yes' : 'No'} | ${target.platform} / ${target.configuration} | ${value ? `${value.status}; ${value.candidate.hash === candidate.hash ? 'current' : 'STALE'}` : 'Not run / unverified'} | ${value ? `[${value.runId}](results/${value.runId}/result.json)` : target.next} |\n`;
}
const ready = releaseReady(matrix.targets,latest,candidate.hash);
text += `\nRelease acceptance: **${ready ? 'Pass' : 'Incomplete'}**. Every required matrix row needs current, verified passing evidence.\n`;
text += '\nOlder development receipts without matrix coordinates are retained but do not establish acceptance.\n';
text += '\nIncomplete attempts and independent evaluation receipts are retained in [attempts/](attempts/).\n';
const destination = path.join(root,'evals/LATEST.md');
if (mode === 'write') await writeFile(destination,text);
else {
  if (await readFile(destination,'utf8') !== text) throw new Error('LATEST.md differs; regenerate with report.mjs write');
  if (!latest.size || [...latest.values()].some(result => result.candidate.hash !== candidate.hash)) throw new Error('Evaluation evidence is absent or stale');
}
if (mode === 'release' && !ready) { console.error('Release incomplete: missing, failed or stale required results'); process.exitCode=1; }
else console.log(`${mode}: report and recorded evidence verified`);
