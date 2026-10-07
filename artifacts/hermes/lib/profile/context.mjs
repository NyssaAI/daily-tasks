import { readFile } from 'node:fs/promises';
import { homedir } from 'node:os';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { expandStoredPath, validateProfile } from './profile.mjs';
import { localDay, utcTimestamp } from '../time/time.mjs';

/** Bind one planning session to explicitly resolved roots, never a subprocess cwd. */
export function planningBinding(input) {
  const roots = ['vaultRoot','projectsRoot','dailyPlansRoot'].map(key => {
    if (typeof input[key] !== 'string' || !path.isAbsolute(input[key])) throw new TypeError(`${key} must be one absolute root`);
    const root = path.normalize(input[key]);
    return process.platform === 'win32' ? root.toLowerCase() : root;
  });
  return createHash('sha256').update(JSON.stringify(roots)).digest('hex');
}

/** CLI scope guard; fingerprints prevent accidental cross-vault reuse, not authorize writes. */
export function assertPlanningScope(input) {
  if (!/^[a-f0-9]{64}$/.test(input.contextBinding ?? '')) throw new TypeError('Resolved contextBinding required for single-vault planning');
  if (planningBinding(input) !== input.contextBinding) throw new Error('Resolved roots differ from the current vault binding; start a separate planning session');
  if (input.inventory && input.inventoryBinding !== input.contextBinding) throw new Error('Inventory binding differs from the current vault; refresh within this session');
  if (input.mapping && Object.keys(input.mapping).length && input.mappingBinding !== input.contextBinding) throw new Error('Numbered review belongs to a different vault binding; open a new review');
}

/** Capture the host's vault binding once. Never use this subprocess's cwd as scope. */
export async function resolveContext(input) {
  const boundVault = input.vaultRoot ?? input.initialCwd;
  const homeRoot = input.homeRoot ?? homedir();
  if (!path.isAbsolute(boundVault ?? '') || !path.isAbsolute(homeRoot)) throw new TypeError('Absolute vaultRoot or captured initialCwd and homeRoot required');
  const candidates = input.profilePath ? [input.profilePath] : input.configRoot ? [path.join(input.configRoot,'profile.json')] :
    [path.join(boundVault,'.nyssaai/daily-tasks/profile.json'),path.join(boundVault,'.nyssa/daily-tasks/profile.json'),
      path.join(homeRoot,'.nyssaai/daily-tasks/profile.json'),path.join(homeRoot,'.nyssa/daily-tasks/profile.json')];
  let profile, profilePath;
  for (const filename of candidates) {
    if (!path.isAbsolute(filename)) throw new TypeError('profilePath/configRoot must be absolute');
    try { profile = JSON.parse((await readFile(filename,'utf8')).replace(/^\uFEFF/,'')); profilePath = filename; break; }
    catch (error) { if (error.code !== 'ENOENT') throw error; }
  }
  if (!profile) return {configured:false,candidates,vaultRoot:boundVault,homeRoot};
  const validation = validateProfile(profile);
  if (!validation.valid) throw new TypeError(validation.errors.join('; '));
  const vaultRoot = expandStoredPath(profile.vaultRoot,boundVault,homeRoot);
  if (path.relative(path.resolve(vaultRoot),path.resolve(boundVault)) !== '') throw new Error('Profile vaultRoot conflicts with the supplied vault binding');
  const configRoot = path.dirname(profilePath);
  const legacyState = path.join(vaultRoot,'.nyssa/daily-tasks');
  const stateRoot = input.stateRoot ?? (path.relative(configRoot,legacyState) === '' ? legacyState : path.join(vaultRoot,'.nyssaai/daily-tasks'));
  if (!path.isAbsolute(stateRoot)) throw new TypeError('stateRoot must be absolute');
  const projectsRoot = expandStoredPath(profile.projectsRoot,vaultRoot,homeRoot);
  const dailyPlansRoot = path.join(vaultRoot,profile.dailyPlansRelative);
  const within = (root,target) => {
    const relative = path.relative(root,target);
    return relative === '' || (relative !== '..' && !relative.startsWith('..' + path.sep) && !path.isAbsolute(relative));
  };
  if ([dailyPlansRoot,projectsRoot].some(target => within(configRoot,target) || within(stateRoot,target))) throw new Error('User output cannot be written beneath configuration/state storage');
  const now = utcTimestamp(input.now ?? new Date().toISOString());
  return {configured:true,profilePath,profile,configRoot,stateRoot,vaultRoot,homeRoot,projectsRoot,dailyPlansRoot,
    planningBinding:planningBinding({vaultRoot,projectsRoot,dailyPlansRoot}),
    timezone:validation.resolvedTimezone,localDate:localDay(now,validation.resolvedTimezone),now,
    templates:Object.fromEntries(Object.entries(profile.templates ?? {}).map(([key,value]) => [key,expandStoredPath(value,vaultRoot,homeRoot)])),
    ttlSeconds:profile.projectIndex?.ttlSeconds ?? 14400};
}
