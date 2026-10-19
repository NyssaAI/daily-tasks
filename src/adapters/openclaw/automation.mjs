import { createHash } from 'node:crypto';
import path from 'node:path';

const duration = /^[1-9]\d*(?:ms|s|m|h|d|w)$/;
const normalized = value => process.platform === 'win32' ? path.normalize(value).toLowerCase() : path.normalize(value);
const sourceIdentity = sources => [sources.schemaVersion,...['user','project'].map(scope => sources[scope].profilePath === null ? null : normalized(path.resolve(sources[scope].profilePath)))];

export function validatePrewarmOptions(input) {
  if (!path.isAbsolute(input.vaultRoot ?? '')) throw new TypeError('vaultRoot must be absolute');
  if (!path.isAbsolute(input.homeRoot ?? '')) throw new TypeError('homeRoot must be absolute');
  if (input.profilePath !== undefined) throw new TypeError('profilePath legacy selector is not supported; use configurationSources');
  if (input.stateRoot !== undefined && !path.isAbsolute(input.stateRoot)) throw new TypeError('stateRoot must be absolute');
  if (input.configurationSources !== undefined) {
    const sources = input.configurationSources;
    if (!sources || sources.schemaVersion !== 1 || Object.keys(sources).some(key => !['schemaVersion','user','project'].includes(key))) throw new TypeError('Invalid configurationSources schemaVersion');
    for (const scope of ['user','project']) {
      const selection = sources[scope];
      if (!selection || Object.keys(selection).length !== 1 || !Object.hasOwn(selection,'profilePath') ||
          (selection.profilePath !== null && (typeof selection.profilePath !== 'string' || !path.isAbsolute(selection.profilePath)))) {
        throw new TypeError(`configurationSources.${scope} requires absolute profilePath or explicit null absence`);
      }
    }
  }
  if (!duration.test(input.every ?? '')) throw new TypeError('every must be one positive OpenClaw duration such as 30m, 1h, or 1d');
}

export function prewarmDeclarationKey(input) {
  validatePrewarmOptions(input);
  const scope = JSON.stringify(input.configurationSources === undefined && input.stateRoot === undefined
    ? [normalized(input.vaultRoot),normalized(input.homeRoot),null]
    : ['context-v1',normalized(path.resolve(input.vaultRoot)),normalized(path.resolve(input.homeRoot)),
      null,
      input.configurationSources === undefined ? null : sourceIdentity(input.configurationSources),
      input.stateRoot === undefined ? null : normalized(path.resolve(input.stateRoot))]);
  return `daily-tasks:project-index-prewarm:${createHash('sha256').update(scope).digest('hex').slice(0,24)}`;
}

export function buildPrewarmAutomation(input) {
  validatePrewarmOptions(input);
  if (!path.isAbsolute(input.nodePath ?? '')) throw new TypeError('nodePath must be absolute');
  if (!path.isAbsolute(input.warmCommandPath ?? '')) throw new TypeError('warmCommandPath must be absolute');
  if (input.gatewayPort !== undefined && (!Number.isInteger(input.gatewayPort) || input.gatewayPort < 1 || input.gatewayPort > 65535)) {
    throw new TypeError('gatewayPort must be an integer from 1 to 65535');
  }
  if (input.gatewayUrl !== undefined) {
    let protocol;
    try { protocol = new URL(input.gatewayUrl).protocol; }
    catch { throw new TypeError('gatewayUrl must be an absolute ws:// or wss:// URL'); }
    if (!['ws:','wss:'].includes(protocol)) throw new TypeError('gatewayUrl must be an absolute ws:// or wss:// URL');
  }
  const declarationKey = prewarmDeclarationKey(input);
  const commandArgv = [
    input.nodePath,
    input.warmCommandPath,
    '--vault-root',input.vaultRoot,
    '--home-root',input.homeRoot,
    ...(input.configurationSources === undefined ? [] : ['--configuration-sources',JSON.stringify(input.configurationSources)]),
    ...(input.stateRoot === undefined ? [] : ['--state-root',input.stateRoot]),
  ];
  const connectionArgs = input.gatewayUrl
    ? ['--url',input.gatewayUrl]
    : input.gatewayPort
      ? ['--port',String(input.gatewayPort)]
      : [];
  const args = [
    'automations',...connectionArgs,'add',
    '--name',`daily-tasks-project-index-prewarm-${declarationKey.split(':').at(-1)}`,
    '--display-name','Daily Tasks project-index prewarm',
    '--description','Cheap stale-on-demand project-index prewarm; correctness remains in each consumer.',
    '--every',input.every,
    '--command-argv',JSON.stringify(commandArgv),
    '--declaration-key',declarationKey,
    '--no-deliver',
    '--timeout-seconds','120',
    '--output-max-bytes','4096',
    ...(input.disabled ? ['--disabled'] : []),
  ];
  return {declarationKey,commandArgv,args,every:input.every,delivery:'none',usesAgent:false};
}
