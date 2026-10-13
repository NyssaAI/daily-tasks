import path from 'node:path';
import { resolveContext } from '../profile/context.mjs';
import { expandStoredPath } from '../profile/profile.mjs';
import { appendDecision } from '../log/decision-log.mjs';
import { uuid7 } from '../identity/identity.mjs';
import { activityTime } from '../time/time.mjs';
import { templateKinds, templateFingerprint, loadTemplateCatalog, identifyTemplate, compareTemplates } from './catalog.mjs';
import { storageHash, readTemplateFile, readTemplateStore, writeTemplateStore, withTemplateLock } from './storage.mjs';
import { templatePlacement } from './placement.mjs';

const policies = ['ask','latest','keep'];
const revisionPattern = /^sha256:[a-f0-9]{64}$/;
const samePath = (a,b) => a && b && path.relative(a,b) === '';
const digest = value => storageHash(JSON.stringify(value));

function validateEntry(kind,entry) {
  if (!templateKinds.includes(kind) || !entry || typeof entry.selector !== 'string' ||
      !entry.active || typeof entry.active.content !== 'string' || entry.active.revision !== templateFingerprint(entry.active.content) ||
      !['observed','accepted','retained','automatic'].includes(entry.origin) ||
      (entry.policy !== undefined && !policies.includes(entry.policy)) ||
      !entry.decisions || typeof entry.decisions !== 'object' || Array.isArray(entry.decisions) ||
      Object.entries(entry.decisions).some(([revision,value]) => !revisionPattern.test(revision) || !['accepted','declined','postponed'].includes(value))) {
    throw new Error(`Invalid retained template: ${kind}`);
  }
  if (entry.upstream && entry.upstream.revision !== templateFingerprint(entry.upstream.content)) throw new Error(`Invalid template origin: ${kind}`);
  if (entry.fileUpdate && (!path.isAbsolute(entry.fileUpdate.path ?? '') ||
      entry.fileUpdate.before !== templateFingerprint(entry.fileUpdate.beforeContent) ||
      entry.fileUpdate.after !== templateFingerprint(entry.fileUpdate.target.content) ||
      entry.fileUpdate.after !== entry.fileUpdate.target.revision)) throw new Error(`Invalid pending template update: ${kind}`);
}

function snapshot(kind,content,catalog,sourcePath = null) {
  const identity = identifyTemplate(kind,content,catalog);
  return {content,revision:identity.revision,source:identity.source,contract:identity.contract,sourcePath};
}

async function inspect(input,options = {}) {
  if (!Array.isArray(input.kinds) || !input.kinds.length || new Set(input.kinds).size !== input.kinds.length || input.kinds.some(kind => !templateKinds.includes(kind))) throw new TypeError('kinds must name distinct supported templates relevant to this request');
  const context = options.context ?? await resolveContext(input);
  if (!context.configured) throw new Error('Resolve Daily Tasks configuration before templates');
  const catalog = options.catalog ?? await loadTemplateCatalog();
  const stores = {};
  for (const [scope,directory] of Object.entries(context.writableScopes)) {
    stores[scope] = await readTemplateStore(directory);
    for (const [kind,entry] of Object.entries(stores[scope].value.templates)) validateEntry(kind,entry);
  }
  const scope = input.scope ?? (stores.legacy ? 'legacy' : stores.project ? 'project' : 'user');
  if (!stores[scope]) throw new Error('Requested template scope is not available in this context');
  const templates = {};
  for (const kind of input.kinds) {
    const available = snapshot(kind,catalog[kind].content,catalog);
    const preferenceSource = context.preferenceSources[`templates.${kind}`] ?? null;
    const configured = context.profile.templates?.[kind];
    if (configured?.startsWith('./') && !context.vaultRoot) throw new Error(`A bound vault is required for templates.${kind}`);
    const sourcePath = configured ? expandStoredPath(configured,context.vaultRoot,context.homeRoot) : null;
    const selector = digest({kind,preferenceSource,sourcePath});
    const sourceContent = sourcePath ? await readTemplateFile(sourcePath) : null;
    const observedRevision = sourceContent === null ? null : templateFingerprint(sourceContent);
    const transient = preferenceSource === 'current-task';
    const bundledSelector = digest({kind,preferenceSource:null,sourcePath:null});
    const matches = Object.entries(stores).reverse().map(([entryScope,store]) => ({scope:entryScope,entry:store.value.templates[kind]}))
      .filter(({entry}) => !transient && entry && (entry.selector === selector ||
        (sourcePath && entry.selector === bundledSelector && entry.active.revision === observedRevision)));
    const chosen = matches.find(({entry}) => entry.origin !== 'observed') ?? matches[0];
    if (sourcePath && sourceContent === null && !chosen) throw new Error(`Configured template is missing: ${sourcePath}; supply a replacement or explicitly reset it`);
    let active = sourceContent !== null ? snapshot(kind,sourceContent,catalog,sourcePath) : chosen?.entry.active ?? available;
    let upstream = chosen?.entry.upstream ??
      (chosen?.entry.active.source !== 'custom' && chosen?.entry.active.revision === active.revision ? {...chosen.entry.active,sourcePath:null} :
        active.source !== 'custom' ? {...active,sourcePath:null} : null);
    let fileUpdate = chosen?.entry.fileUpdate ?? null;
    // Older receipts adopted JSON content while leaving the configured file unchanged.
    // Preserve that explicit choice as an unfinished file effect, never hide the file.
    if (!fileUpdate && sourceContent !== null && chosen?.entry.origin === 'accepted' &&
        !chosen.entry.upstream && chosen.entry.observedRevision === observedRevision &&
        chosen.entry.active.revision !== observedRevision) {
      fileUpdate = {path:sourcePath,before:observedRevision,beforeContent:sourceContent,
        after:chosen.entry.active.revision,target:chosen.entry.active};
    }
    if (fileUpdate) {
      if (fileUpdate.path !== sourcePath) throw new Error('Pending template update belongs to another file');
      fileUpdate = {...fileUpdate,status:observedRevision === fileUpdate.after ? 'applied' : observedRevision === fileUpdate.before ? 'pending' : 'conflict'};
      if (fileUpdate.status === 'applied') upstream = fileUpdate.target;
    }
    let origin = chosen?.entry.origin ?? 'observed';
    const policy = matches.find(({entry}) => entry.policy !== undefined)?.entry.policy ?? 'ask';
    const decisions = Object.assign({},...matches.toReversed().map(({entry}) => entry.decisions));
    const changed = (upstream?.revision ?? active.revision) !== available.revision;
    const activeContract = active.contract ?? (active.revision === upstream?.revision ? upstream.contract : null);
    const compatible = activeContract !== null && activeContract === available.contract;
    const automatic = changed && policy === 'latest' && compatible && !fileUpdate && decisions[available.revision] !== 'declined';
    const automaticBlocked = changed && policy === 'latest' && !compatible;
    if (automatic && !sourcePath) { active = available; upstream = available; origin = 'automatic'; }
    const shouldOffer = changed && !automatic && !fileUpdate && (input.review === true ||
      ((policy === 'ask' || automaticBlocked) && decisions[available.revision] !== 'declined'));
    templates[kind] = {kind,selector,retainedSelector:chosen?.entry.selector ?? null,observedRevision:observedRevision ?? chosen?.entry.observedRevision ?? null,
      active,available,upstream,sourcePath,fileUpdate,origin,policy,decisions,shouldOffer,automatic,automaticBlocked,
      compatibility:compatible ? 'compatible' : activeContract === null ? 'custom-review-required' : 'record-contract-changed',
      comparison:{...compareTemplates(active.content,available.content),
        customized:upstream ? active.revision !== upstream.revision : active.source === 'custom',
        localChanges:upstream ? compareTemplates(upstream.content,active.content) : null,
        bundledChanges:upstream ? compareTemplates(upstream.content,available.content) : null},
      activeScope:chosen?.scope ?? null,
      baselineScope:sourcePath && chosen?.entry.selector === selector ? chosen.scope : scope,
      transient,sourceUnavailable:!!sourcePath && sourceContent === null,
      explanation:!chosen && !sourcePath ? 'First observation of the installed template; earlier acceptance is unknown.' :
        sourcePath && active.source === 'bundled-copy' ? 'Configured file matches a verified earlier bundled template.' : null};
  }
  const storage = Object.fromEntries(Object.entries(stores).map(([key,store]) => [key,{path:store.path,sha256:store.sha256}]));
  const token = digest({scope,storage,templates:Object.fromEntries(Object.entries(templates).map(([kind,value]) => [kind,
    {selector:value.selector,observedRevision:value.observedRevision,available:value.available.revision,contract:value.available.contract}]))});
  const pendingScopes = Object.entries(stores).filter(([,store]) => store.value.pending).map(([key]) => key);
  const packet = {status:pendingScopes.length ? 'recovery-required' : 'prepared',scope,token,templates,storage,pendingScopes,
    placement:await templatePlacement(context,templates),
    context:{configurationSources:context.configurationSources,profilePath:context.configurationSources ? undefined : context.profilePath,
      homeRoot:context.homeRoot,vaultRoot:context.vaultRoot,stateRoot:context.stateRoot,preferenceOverrides:context.preferenceOverrides}};
  return {packet,context,stores};
}

/** Read-only preparation. The caller renders the comparison and authors documents. */
export async function prepareTemplates(input,options) { return (await inspect(input,options)).packet; }

function savedEntry(row,previous) {
  const sameSource = previous && (previous.selector === row.selector || previous.selector === row.retainedSelector);
  const copiedBinding = row.retainedSelector && row.retainedSelector !== row.selector;
  return {selector:row.selector,observedRevision:row.observedRevision,active:row.active,upstream:row.upstream,origin:row.origin,
    ...(row.fileUpdate && row.fileUpdate.status !== 'applied' ? {fileUpdate:row.fileUpdate} : {}),
    ...(copiedBinding ? {policy:row.policy} : sameSource && previous.policy !== undefined ? {policy:previous.policy} : {}),
    decisions:copiedBinding ? row.decisions : sameSource ? previous.decisions : {}};
}

function summarize(entries) {
  return Object.fromEntries(Object.entries(entries).map(([kind,entry]) => [kind,{revision:entry.active.revision,pendingRevision:entry.fileUpdate?.after ?? null,origin:entry.origin,policy:entry.policy ?? null,decisions:entry.decisions}]));
}

function queueFileUpdate(row,entry) {
  if (row.sourceUnavailable) throw new Error('Restore the missing template file before upgrading it');
  entry.fileUpdate = {path:row.sourcePath,before:row.active.revision,beforeContent:row.active.content,
    after:row.available.revision,target:row.available};
}

function saveResult(store,scope,status) {
  const pendingFileUpdates = Object.entries(store.value.templates).filter(([,entry]) => entry.fileUpdate).map(([kind]) => kind);
  return {status:pendingFileUpdates.length ? 'file-update-required' : status,scope,path:store.path,pendingFileUpdates};
}

async function finishPending(store,context) {
  const pending = store.value.pending;
  if (!pending) return;
  if (!context.projectsRoot || !samePath(pending.projectsRoot,context.projectsRoot)) throw new Error('Pending template event belongs to another project collection');
  await appendDecision({projectsRoot:context.projectsRoot,entry:pending.event});
  const value = structuredClone(store.value);
  delete value.pending;
  await writeTemplateStore(store,value);
}

/** Save retained JSON snapshots or explicit choices; project choices use the log CLI boundary. */
export async function saveTemplateState(input,options) {
  if (!['baseline','decide','recover'].includes(input.action)) throw new TypeError('Unknown template-state action');
  const loaded = await inspect(input,options);
  const {packet,context} = loaded;
  if (typeof input.expectedToken !== 'string') throw new TypeError('expectedToken from template-prepare is required');
  const decisions = input.decisions ?? [];
  if (!Array.isArray(decisions) || (input.action === 'decide' && !decisions.length) || (input.action !== 'decide' && decisions.length)) throw new TypeError('Explicit decisions required only for decide');
  if (new Set(decisions.map(item => item.kind)).size !== decisions.length) throw new TypeError('One decision per template kind');
  for (const decision of decisions) {
    if (!input.kinds.includes(decision.kind) || !['accept','decline','postpone','review','set-policy','reset'].includes(decision.action) ||
        (decision.action === 'set-policy' ? !policies.includes(decision.policy) : decision.policy !== undefined)) throw new TypeError('Invalid template decision');
  }
  if (input.action === 'decide' && (typeof input.originalWords !== 'string' || !input.originalWords.trim())) throw new TypeError('Explicit originalWords required for template choices');
  if (Object.values(packet.templates).some(row => row.transient)) throw new Error('One-off template overrides cannot be persisted');
  if (packet.scope === 'user' && decisions.some(({kind}) => context.preferenceSources[`templates.${kind}`] && context.preferenceSources[`templates.${kind}`] === context.configurationSources?.project.profilePath)) throw new Error('Project template overrides personal scope; use a personal-only context to change user defaults');
  const requestHash = digest({action:input.action,kinds:input.kinds,scope:packet.scope,decisions,originalWords:input.originalWords,expectedToken:input.expectedToken});
  const initialStore = loaded.stores[packet.scope];
  const replay = initialStore.value.lastRequest === requestHash;
  if (!replay && input.expectedToken !== packet.token) throw new Error('Template sources or choices changed; prepare again');
  if (input.dryRun) return {status:'preview',scope:packet.scope,path:initialStore.path,templates:packet.templates,decisions};
  return withTemplateLock(initialStore,async () => {
    const fresh = await inspect(input,options);
    const store = fresh.stores[packet.scope];
    if (store.value.lastRequest === requestHash) {
      await finishPending(store,fresh.context);
      return saveResult(store,packet.scope,'unchanged');
    }
    if (fresh.packet.token !== input.expectedToken) throw new Error('Template sources or choices changed; prepare again');
    if (input.action === 'recover') {
      await finishPending(store,fresh.context);
      return saveResult(store,packet.scope,'recovered');
    }
    if (fresh.packet.pendingScopes.length) throw new Error('Recover pending template choices before writing');
    if (input.action === 'baseline') {
      const inherited = Object.values(fresh.packet.templates).find(row => row.baselineScope !== packet.scope);
      if (inherited) throw new Error(`Save the ${inherited.kind} baseline in its owning ${inherited.baselineScope} scope; prepare again with that scope`);
    }
    const cancellations = new Set(decisions.filter(decision => ['decline','reset'].includes(decision.action)).map(decision => decision.kind));
    if (Object.values(fresh.packet.templates).some(row => row.fileUpdate?.status === 'conflict' && !cancellations.has(row.kind))) throw new Error('Pending template file update conflicts with actual content; preserve it and resolve before saving');
    if (decisions.some(decision => fresh.packet.templates[decision.kind].fileUpdate?.status === 'pending' && !cancellations.has(decision.kind))) throw new Error('Finish the pending template file update before changing its decision');
    const value = structuredClone(store.value);
    for (const row of Object.values(fresh.packet.templates)) {
      if (input.action === 'baseline' && row.activeScope && !row.sourcePath && !row.automatic) continue;
      if (input.action === 'decide' && !decisions.some(decision => decision.kind === row.kind)) continue;
      value.templates[row.kind] = savedEntry(row,value.templates[row.kind]);
      if (input.action === 'baseline' && row.automatic && row.sourcePath) queueFileUpdate(row,value.templates[row.kind]);
    }
    for (const decision of decisions) {
      const row = fresh.packet.templates[decision.kind], entry = value.templates[decision.kind];
      if (decision.action === 'reset') { delete value.templates[decision.kind]; continue; }
      if (decision.action === 'accept') {
        if (row.sourcePath && row.active.revision !== row.available.revision) queueFileUpdate(row,entry);
        else { entry.active = row.available; entry.upstream = row.available; }
        entry.origin = 'accepted';
        entry.decisions[row.available.revision] = 'accepted';
      } else if (decision.action === 'decline') {
        entry.origin = 'retained'; entry.decisions[row.fileUpdate?.after ?? row.available.revision] = 'declined';
        delete entry.fileUpdate;
      } else if (decision.action === 'postpone') entry.decisions[row.available.revision] = 'postponed';
      else if (decision.action === 'review') delete entry.decisions[row.available.revision];
      else {
        entry.policy = decision.policy;
        if (decision.policy === 'keep') entry.origin = 'retained';
      }
    }
    if (JSON.stringify(value.templates) === JSON.stringify(store.value.templates)) return saveResult(store,packet.scope,'unchanged');
    value.lastRequest = requestHash;
    const meaningful = decisions.some(decision => !['postpone','review'].includes(decision.action));
    if (meaningful && packet.scope !== 'user' && !fresh.context.preferenceOnly) {
      if (!fresh.context.projectsRoot) throw new Error('Project template decisions require a resolved project collection');
      const timing = activityTime(undefined,fresh.context.now);
      value.pending = {projectsRoot:fresh.context.projectsRoot,event:{id:uuid7(),operation_id:uuid7(),action:'templates.changed',record_ids:[],
        actor:{kind:'person',id:fresh.context.profile.user.email},...timing,original_words:input.originalWords,
        before:summarize(store.value.templates),after:summarize(value.templates)}};
    }
    // Protect all participating scope stores and configured template content, not only the target.
    if ((await inspect(input,options)).packet.token !== input.expectedToken) throw new Error('Template sources changed before save');
    await writeTemplateStore(store,value);
    await finishPending(store,fresh.context);
    return saveResult(store,packet.scope,'saved');
  });
}
