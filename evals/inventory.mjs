import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { root, tree, digest } from '../scripts/assemble.mjs';

export async function inventory() {
  const files = new Map();
  for (const folder of ['skills','lib','bin','scripts','test','evals','artifacts','.github','.claude-plugin','.codex-plugin','.cursor-plugin']) {
    for (const [name,value] of await tree(path.join(root,folder),folder+'/')) {
      if (/^evals\/(results|attempts)\//.test(name) || name === 'evals/LATEST.md') continue;
      files.set(name,value);
    }
  }
  for (const name of ['.gitattributes','plugin.json','package.json','capabilities.json','AGENTS.md','README.md','docs/requirements.md','docs/executable-contract.md','docs/host-support.md']) files.set(name,(await readFile(path.join(root,name),'utf8')).replaceAll('\r\n','\n'));
  return {hash:digest(files),files:Object.fromEntries([...files].map(([name,value]) => [name,createHash('sha256').update(value).digest('hex')]))};
}
