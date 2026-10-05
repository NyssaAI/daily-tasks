import { mkdir, writeFile, readFile } from 'node:fs/promises';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { root } from '../scripts/assemble.mjs';
import { inventory } from './inventory.mjs';
import { deterministicCommands } from './evidence.mjs';

const before = await inventory();
const matrix = JSON.parse(await readFile(path.join(root,'evals/matrix.json'),'utf8'));
const target = matrix.targets.find(item => item.kind === 'deterministic' && item.platform === `${process.platform}/${process.arch}`);
if (!target) throw new Error('No declared matrix row for this platform');
const runId = new Date().toISOString().replaceAll(/[:.]/g,'-')+'-'+process.pid;
const directory = path.join(root,'evals/results',runId);
await mkdir(directory,{recursive:true});
const results = [];
for (const command of deterministicCommands) {
  const result = spawnSync(process.execPath,command.slice(1),{cwd:root,encoding:'utf8',maxBuffer:8*1024*1024});
  const output = `stdout:\n${result.stdout || ''}\nstderr:\n${result.stderr || ''}\nerror:${result.error?.message || ''}\n`;
  const filename = `command-${results.length+1}.txt`;
  await writeFile(path.join(directory,filename),output);
  results.push({command,exit:result.status,output:filename,sha256:createHash('sha256').update(output).digest('hex')});
}
const after = await inventory();
const result = {runId,target:target.id,suite:target.suite,configuration:target.configuration,completed_at:new Date().toISOString(),kind:'deterministic',platform:target.platform,node:process.version,candidate:before,status:results.every(r => r.exit === 0) && before.hash === after.hash ? 'pass' : 'fail',source_unchanged:before.hash === after.hash,commands:results};
await writeFile(path.join(directory,'result.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({runId,status:result.status,candidate:before.hash}));
if (result.status !== 'pass') process.exitCode=1;
