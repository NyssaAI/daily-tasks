import { readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import { root, tree } from './assemble.mjs';

const files = await tree(path.join(root,'skills'),'skills/');
const errors = [];
const names = new Set();
for (const [name,content] of files) {
  if (name.endsWith('/SKILL.md')) {
    const match = /^---\nname: ([a-z0-9-]+)\ndescription: ([^\n]+)\n---/.exec(content);
    if (!match || match[1] !== path.basename(path.dirname(name)) || names.has(match[1])) errors.push(`Invalid skill frontmatter: ${name}`);
    else names.add(match[1]);
  }
  for (const match of content.matchAll(/\[[^\]]+\]\(([^)]+)\)/g)) {
    if (/^(https?:|#)/.test(match[1])) continue;
    const target = path.resolve(root,path.dirname(name),match[1].split('#')[0]);
    if (!target.startsWith(root+path.sep)) { errors.push(`Escaping link: ${name}`); continue; }
    try { await stat(target); } catch { errors.push(`Broken link in ${name}: ${match[1]}`); }
  }
  if (/C:[\\/]|D:[\\/]|\.codex\/plugins\/cache/.test(content)) errors.push(`Local path leaked: ${name}`);
}
const identity = JSON.parse(await readFile(path.join(root,'plugin.json'),'utf8'));
const packageInfo = JSON.parse(await readFile(path.join(root,'package.json'),'utf8'));
if (identity.version !== packageInfo.version || names.size !== 6) errors.push('Version or skill inventory mismatch');
const capabilities = JSON.parse(await readFile(path.join(root,'capabilities.json'),'utf8'));
if (!capabilities.operations?.length) errors.push('Missing executable contract');
if (errors.length) throw new Error(errors.join('\n'));
console.log(`Validated ${names.size} skills, relative links, identity and executable contract`);
