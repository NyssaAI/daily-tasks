import { readdir, lstat } from 'node:fs/promises';
import path from 'node:path';
import { templateFiles } from './catalog.mjs';
import { readTemplateFile } from './storage.mjs';

/** Propose skill-owned template placement; never create directories, files or preferences. */
export async function templatePlacement(context,templates) {
  if (!context.vaultRoot) return {status:'unbound',templates:{}};
  const entries = await readdir(context.vaultRoot,{withFileTypes:true});
  const roles = Object.fromEntries(['projects','areas','resources','archives'].map(role => [role,[]]));
  for (const entry of entries) {
    const role = entry.name.toLowerCase().replace(/^\d+[ ._-]+/,'').replace(/^archive$/,'archives');
    if (roles[role]) roles[role].push(entry);
  }
  if (Object.values(roles).some(matches => !matches.length)) return {status:'not-para',templates:{}};
  if (Object.values(roles).some(matches => matches.length !== 1)) return {status:'ambiguous',templates:{}};
  for (const [entry] of Object.values(roles)) {
    const stats = await lstat(path.join(context.vaultRoot,entry.name));
    if (!stats.isDirectory() || stats.isSymbolicLink()) return {status:'unsafe',templates:{}};
  }
  const directory = path.join(context.vaultRoot,roles.resources[0].name,'templates');
  const proposed = {};
  for (const [kind,row] of Object.entries(templates)) {
    if (row.transient) { proposed[kind] = {status:'one-off'}; continue; }
    if (row.sourcePath) { proposed[kind] = {status:'configured',path:row.sourcePath}; continue; }
    if (context.preferenceSources[`templates.${kind}`]) { proposed[kind] = {status:'bundled-reset'}; continue; }
    const filename = path.join(directory,templateFiles[kind]);
    const existing = await readTemplateFile(filename);
    proposed[kind] = {status:existing === null ? 'create' : 'existing',path:filename,
      profileValue:'./'+path.relative(context.vaultRoot,filename).split(path.sep).join('/'),
      content:row.active.content,revision:row.active.revision};
  }
  return {status:'para',directory,templates:proposed};
}
