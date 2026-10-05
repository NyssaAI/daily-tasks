import { readdir, readFile, writeFile, mkdir, lstat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';

export const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const encode = value => JSON.stringify(value, null, 2) + '\n';
export async function tree(directory, prefix = '') {
  const files = new Map();
  for (const item of (await readdir(directory, { withFileTypes: true })).sort((a,b) => a.name.localeCompare(b.name))) {
    const name = prefix + item.name;
    if (item.isSymbolicLink()) throw new Error(`Symlink cannot be packaged: ${name}`);
    if (item.isDirectory()) for (const [key,value] of await tree(path.join(directory,item.name),name+'/')) files.set(key,value);
    else files.set(name, (await readFile(path.join(directory,item.name),'utf8')).replaceAll('\r\n','\n'));
  }
  return files;
}
export function digest(files) {
  const hash = createHash('sha256');
  for (const [name,value] of [...files].sort(([a],[b]) => a.localeCompare(b))) hash.update(name+'\0'+value+'\0');
  return hash.digest('hex');
}
export async function buildPackages() {
  const identity = JSON.parse(await readFile(path.join(root,'plugin.json'),'utf8'));
  const {$schema,...host} = identity;
  const manifests = new Map([
    ['.claude-plugin/plugin.json', encode(host)],
    ['.cursor-plugin/plugin.json', encode(host)],
    ['.codex-plugin/plugin.json', encode({...host,skills:'./skills/',interface:{displayName:'Daily Tasks',shortDescription:'Personal tasks and daily planning',developerName:'NyssaAI',category:'Productivity'}})],
  ]);
  const shared = new Map([['plugin.json',encode(identity)],['LICENSE',await readFile(path.join(root,'LICENSE'),'utf8')]]);
  for (const folder of ['skills','lib','bin']) for (const [key,value] of await tree(path.join(root,folder),folder+'/')) shared.set(key,value);
  for (const name of ['package.json','capabilities.json']) shared.set(name,await readFile(path.join(root,name),'utf8'));
  const portable = new Map([...shared,...manifests]);
  const agy = new Map(shared); agy.set('plugin.json',encode({name:identity.name,description:identity.description}));
  const cowork = new Map(portable);
  cowork.set('scripts/daily-tasks.mjs',cowork.get('bin/daily-tasks.mjs')); cowork.delete('bin/daily-tasks.mjs');
  for (const [key,value] of cowork) if (key.startsWith('skills/') || key === 'capabilities.json') cowork.set(key,value.replaceAll('bin/daily-tasks.mjs','scripts/daily-tasks.mjs'));
  const hermes = new Map(shared);
  hermes.delete('plugin.json');
  hermes.set('plugin.yaml',`name: daily-tasks\nversion: "${identity.version}"\ndescription: ${JSON.stringify(identity.description)}\n`);
  hermes.set('__init__.py',`from pathlib import Path\n\ndef register(ctx):\n    for skill in sorted((Path(__file__).resolve().parent / "skills").glob("*/SKILL.md")):\n        ctx.register_skill(skill.parent.name, skill)\n`);
  const packages = new Map([['portable',portable],['antigravity',agy],['cowork',cowork],['hermes',hermes]]);
  for (const [format,files] of packages) files.set('assembly.json',encode({format,version:identity.version,source_sha256:digest(files)}));
  return {manifests,packages};
}

async function main() {
  const mode = process.argv[2];
  if (!['write','check'].includes(mode)) throw new Error('Use assemble.mjs write|check');
  const {manifests,packages} = await buildPackages();
  const outputs = new Map(manifests);
  for (const [format,files] of packages) for (const [key,value] of files) outputs.set(`artifacts/${format}/${key}`,value);
  const mismatches = [];
  for (const [relative,content] of outputs) {
    const destination = path.join(root,relative);
    // Every generated ancestor must be an ordinary directory inside this checkout.
    for (let current = destination; current !== root; current = path.dirname(current)) {
      try { if ((await lstat(current)).isSymbolicLink()) throw new Error(`Unsafe generated path: ${current}`); }
      catch (error) { if (error.code !== 'ENOENT') throw error; }
    }
    if (mode === 'write') { await mkdir(path.dirname(destination),{recursive:true}); await writeFile(destination,content); }
    else { try { if ((await readFile(destination,'utf8')).replaceAll('\r\n','\n') !== content.replaceAll('\r\n','\n')) mismatches.push(relative); } catch { mismatches.push(relative); } }
  }
  for (const [format,files] of packages) {
    const actual = await tree(path.join(root,'artifacts',format));
    for (const name of actual.keys()) if (!files.has(name)) mismatches.push(`Unexpected artifact: ${format}/${name}`);
  }
  if (mismatches.length) throw new Error(mismatches.join('\n'));
  console.log(`${mode}: ${outputs.size} generated files match canonical source`);
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main().catch(error => {console.error(error.message);process.exitCode=1;});
