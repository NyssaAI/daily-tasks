import { readFile, readdir, lstat } from 'node:fs/promises';
import { homedir } from 'node:os';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { expandStoredPath, validatePreferenceLayer, validateEffectiveProfile } from './profile.mjs';
import { localDay, utcTimestamp } from '../time/time.mjs';

/** Bind one planning session to explicitly resolved roots, never a subprocess cwd. */
export function planningBinding(input) {
  const rootKey = (input.workspaceRoot !== undefined && input.vaultRoot === undefined) ? 'workspaceRoot' : 'vaultRoot';
  const roots = [rootKey,'projectsRoot','dailyPlansRoot'].map(key => {
    if (typeof input[key] !== 'string' || !path.isAbsolute(input[key])) throw new TypeError(`${key} must be one absolute root`);
    const root = path.normalize(input[key]);
    return process.platform === 'win32' ? root.toLowerCase() : root;
  });
  return createHash('sha256').update(JSON.stringify(roots)).digest('hex');
}

/** CLI scope guard; fingerprints prevent accidental cross-workspace reuse, not authorize writes. */
export function assertPlanningScope(input) {
  if (!/^[a-f0-9]{64}$/.test(input.contextBinding ?? '')) throw new TypeError('Resolved contextBinding required for single-workspace planning');
  if (planningBinding(input) !== input.contextBinding) throw new Error('Resolved roots differ from the current workspace binding; start a separate planning session');
  if (input.inventory && input.inventoryBinding !== input.contextBinding) throw new Error('Inventory binding differs from the current workspace; refresh within this session');
  if (input.mapping && Object.keys(input.mapping).length && input.mappingBinding !== input.contextBinding) throw new Error('Numbered review belongs to a different vault binding (workspace binding); open a new review');
}

/** Capture the host's workspace binding once. Never use this subprocess's cwd as scope. */
export async function resolveContext(input) {
  const boundWorkspace = input.workspaceRoot ?? input.vaultRoot ?? input.initialCwd;
  const homeRoot = input.homeRoot ?? homedir();
  if ((boundWorkspace !== undefined && !path.isAbsolute(boundWorkspace)) || !path.isAbsolute(homeRoot)) throw new TypeError('Absolute workspaceRoot/vaultRoot or captured initialCwd and homeRoot required');
  if (!boundWorkspace && !input.homeRoot) throw new TypeError('Explicit homeRoot required for personal preferences without workspaceRoot/vaultRoot or initialCwd');
  if (input.profilePath !== undefined || input.configRoot !== undefined) throw new TypeError('profilePath and configRoot legacy selectors are not supported; use configurationSources');
  const candidates = [], diagnostics = [];
  const documents = new Map();
  const loadProfile = async filename => {
    const normalized = path.normalize(filename);
    const key = process.platform === 'win32' ? normalized.toLowerCase() : normalized;
    if (!documents.has(key)) documents.set(key,await readProfile(filename));
    return documents.get(key);
  };
  const descriptor = input.configurationSources;
  if (descriptor !== undefined && (!descriptor || descriptor.schemaVersion !== 1 || Object.keys(descriptor).some(key => !['schemaVersion','user','project'].includes(key)))) throw new TypeError('Invalid configurationSources schemaVersion');
  const configurationSources = {schemaVersion:1};
  const layers = [];
  for (const [scope,root] of [['user',homeRoot],['project',boundWorkspace]]) {
    let filename = null;
    let selectedProfile;
    if (descriptor !== undefined) {
      const selection = descriptor[scope];
      if (!selection || Object.keys(selection).length !== 1 || !Object.hasOwn(selection,'profilePath') || (selection.profilePath !== null && (typeof selection.profilePath !== 'string' || !path.isAbsolute(selection.profilePath)))) throw new TypeError(`configurationSources.${scope} requires absolute profilePath or explicit null absence`);
      filename = selection.profilePath;
      if (filename && !root) throw new TypeError(`Bound ${scope} root required for configurationSources`);
      // Custom accepted pointers are allowed, but conventional paths cannot select another scope.
      if (filename && /[\\/]\.nyssa-ai[\\/]daily-tasks[\\/]profile\.json$/i.test(filename) && !configurationPaths(root).some(candidate => samePath(candidate,filename))) throw new Error(`configurationSources.${scope} conflicts with the bound scope`);
    } else if (root) {
      for (const candidate of configurationPaths(root)) {
        candidates.push(candidate);
        if (!filename) {
          selectedProfile = await loadProfile(candidate);
          if (selectedProfile) filename = candidate;
        }
        else {
          try {
            await lstat(candidate);
            diagnostics.push({code:'shadowed-configuration',scope,path:candidate,selected:filename});
          } catch (error) { if (error.code !== 'ENOENT') throw error; }
        }
      }
    }
    configurationSources[scope] = {profilePath:filename};
    if (filename) {
      let value = selectedProfile ?? await loadProfile(filename);
      if (!value) throw new Error(`Bound configuration source missing: ${filename}`);
      if (scope === 'user') {
        const validation = validatePreferenceLayer(value);
        if (!validation.valid) throw new TypeError(`${filename}: ${validation.errors.join('; ')}`);
        // Stored documents may serve both scopes; user views never inherit bindings.
        value = Object.fromEntries(Object.entries(value).filter(([key]) => ['schema_version','user','timezone','priorities','templates','projectIndex'].includes(key)));
      }
      layers.push({scope,profilePath:filename,value});
    }
  }
  if (input.preferenceOverrides !== undefined) {
    if (!input.preferenceOverrides || typeof input.preferenceOverrides !== 'object' || Array.isArray(input.preferenceOverrides) || Object.hasOwn(input.preferenceOverrides,'schema_version')) throw new TypeError('preferenceOverrides must contain supported preference fields only');
    const value = {...input.preferenceOverrides,schema_version:2};
    const validation = validatePreferenceLayer(value,'user');
    if (!validation.valid) throw new TypeError(validation.errors.join('; '));
    layers.push({scope:'user',profilePath:null,value});
  }
  let profile = {schema_version:2,timezone:'system',priorities:[],vaultRoot:'.',dailyPlansRelative:'2-areas/daily-plans',templates:{},projectIndex:{ttlSeconds:14400},sources:{autoScan:false,directories:[],mcps:[]}};
  const preferenceSources = {};
  for (const layer of layers) {
    const validation = validatePreferenceLayer(layer.value,layer.scope);
    if (!validation.valid) throw new TypeError(`${layer.profilePath}: ${validation.errors.join('; ')}`);
    for (const [key,value] of Object.entries(layer.value)) {
      if (key === 'schema_version') continue;
      if (['user','templates','projectIndex'].includes(key)) {
        profile[key] = {...profile[key]};
        for (const [leaf,item] of Object.entries(value)) {
          preferenceSources[`${key}.${leaf}`] = layer.profilePath ?? 'current-task';
          if (key === 'templates' && item === null) delete profile.templates[leaf];
          else profile[key][leaf] = item === null ? 14400 : item;
        }
      } else if (key === 'sources') {
        if (value === null) profile.sources = {autoScan:false,directories:[],mcps:[]};
        else profile.sources = {...profile.sources,...value};
        preferenceSources[key] = layer.profilePath ?? 'current-task';
      } else {
        profile[key] = value === null ? (key === 'timezone' ? 'system' : []) : value;
        preferenceSources[key] = layer.profilePath ?? 'current-task';
      }
    }
  }
  const profilePath = layers.filter(layer => layer.profilePath).at(-1)?.profilePath;
  const configRoot = profilePath ? path.dirname(profilePath) : path.join(boundWorkspace ?? homeRoot,'.nyssa-ai/daily-tasks');
  const writableScopes = {user:path.dirname(configurationSources.user.profilePath ?? path.join(homeRoot,'.nyssa-ai/daily-tasks/profile.json')),
    ...(boundWorkspace ? {project:path.dirname(configurationSources.project.profilePath ?? path.join(boundWorkspace,'.nyssa-ai/daily-tasks/profile.json'))} : {})};
  const sharedScopes = writableScopes.project && samePath(writableScopes.user,writableScopes.project)
    ? [{scopes:['user','project'],directory:writableScopes.user}] : [];
  const base = {configurationSources,preferenceOverrides:input.preferenceOverrides,profilePath,configRoot,writableScopes,sharedScopes,candidates,diagnostics,preferenceSources,homeRoot,vaultRoot:boundWorkspace,workspaceRoot:boundWorkspace,profile};
  if (!layers.length) return {...base,configured:false};
  if (!boundWorkspace) {
    const personal = validatePreferenceLayer({schema_version:2,...(profile.user ? {user:profile.user} : {}),timezone:profile.timezone,priorities:profile.priorities,templates:profile.templates,projectIndex:profile.projectIndex});
    if (!personal.valid) throw new TypeError(personal.errors.join('; '));
    const timezone = personal.resolvedTimezone;
    return {...base,configured:!!profile.user?.name && !!profile.user?.email,preferenceOnly:true,timezone};
  }
  const validation = validateEffectiveProfile(profile);
  if (!validation.valid) return {...base,configured:false,missing:validation.errors};
  const workspaceRoot = expandStoredPath(profile.workspaceRoot ?? profile.vaultRoot,boundWorkspace,homeRoot);
  if (!samePath(workspaceRoot,boundWorkspace)) throw new Error('Profile vaultRoot conflicts with the supplied vault binding');
  const stateRoot = await resolveStateRoot(workspaceRoot,input.stateRoot);
  const projectsRoot = expandStoredPath(profile.projectsRoot,workspaceRoot,homeRoot);
  const dailyPlansRoot = path.join(workspaceRoot,profile.dailyPlansRelative);
  const within = (root,target) => {
    const relative = path.relative(root,target);
    return relative === '' || (relative !== '..' && !relative.startsWith('..' + path.sep) && !path.isAbsolute(relative));
  };
  const configurationRoots = [...new Set([configRoot,...layers.filter(layer => layer.profilePath).map(layer => path.dirname(layer.profilePath))])];
  if ([dailyPlansRoot,projectsRoot].some(target => configurationRoots.some(root => within(root,target)) || within(stateRoot,target))) throw new Error('User output cannot be written beneath configuration/state storage');
  const now = utcTimestamp(input.now ?? new Date().toISOString());
  return {...base,configured:true,configurationRoots,profile,stateRoot,workspaceRoot,vaultRoot:workspaceRoot,projectsRoot,dailyPlansRoot,
    planningBinding:planningBinding({workspaceRoot,vaultRoot:workspaceRoot,projectsRoot,dailyPlansRoot}),
    timezone:validation.resolvedTimezone,localDate:localDay(now,validation.resolvedTimezone),now,
    templates:Object.fromEntries(Object.entries(profile.templates ?? {}).map(([key,value]) => [key,expandStoredPath(value,workspaceRoot,homeRoot)])),
    ttlSeconds:profile.projectIndex?.ttlSeconds ?? 14400};
}

const samePath = (left,right) => path.relative(path.resolve(left),path.resolve(right)) === '';
const configurationPaths = root => [path.join(root,'.nyssa-ai/daily-tasks/profile.json')];
async function readProfile(filename) {
  try {
    const value = JSON.parse((await readFile(filename,'utf8')).replace(/^\uFEFF/,''));
    if (!value || typeof value !== 'object' || Array.isArray(value)) throw new TypeError(`Profile must be an object: ${filename}`);
    return value;
  }
  catch (error) { if (error.code === 'ENOENT') return null; throw error; }
}

async function stateContents(directory,prefix = '') {
  let entries;
  try {
    if ((await lstat(directory)).isSymbolicLink()) throw new Error(`Unsafe state directory: ${directory}`);
    entries = await readdir(directory,{withFileTypes:true});
  } catch (error) { if (error.code === 'ENOENT') return []; throw error; }
  const contents = [];
  for (const entry of entries.sort((a,b) => a.name.localeCompare(b.name))) {
    if (!prefix && ['profile.json','templates','cache','project-index.json','project-index-freshness.json'].includes(entry.name)) continue;
    if (entry.name.startsWith('.') || entry.name.endsWith('.tmp')) continue;
    const filename = path.join(directory,entry.name), relative = prefix+entry.name;
    if (entry.isSymbolicLink()) throw new Error(`Unsafe state entry: ${filename}`);
    if (entry.isDirectory()) contents.push(...await stateContents(filename,relative+'/'));
    else if (entry.name.endsWith('.json')) contents.push([relative,createHash('sha256').update(await readFile(filename)).digest('hex')]);
  }
  return contents;
}

async function resolveStateRoot(vaultRoot,explicit) {
  if (explicit !== undefined && !path.isAbsolute(explicit)) throw new TypeError('stateRoot must be absolute');
  const roots = configurationPaths(vaultRoot).map(filename => path.dirname(filename));
  if (explicit && !roots.some(root => samePath(root,explicit))) roots.unshift(explicit);
  const stores = [];
  for (const root of roots) {
    const contents = await stateContents(root);
    if (contents.length) stores.push({root,identity:JSON.stringify(contents)});
  }
  if (new Set(stores.map(store => store.identity)).size > 1) throw new Error('Conflicting authoritative state stores require explicit reconciliation before writes');
  if (explicit && stores.length && !stores.some(store => samePath(store.root,explicit))) {
    throw new Error(`Explicit state root ${explicit} has no authoritative history; existing state is at ${stores.map(store => store.root).join(', ')}. Reopen with the established state root or explicitly reconcile the stores before writes.`);
  }
  if (explicit) return explicit;
  if (stores.length) return stores[0].root;
  return roots[0];
}
