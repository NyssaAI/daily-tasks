import { createHash } from 'node:crypto';
import path from 'node:path';

const duration = /^[1-9]\d*(?:ms|s|m|h|d|w)$/;
const normalized = value => process.platform === 'win32' ? path.normalize(value).toLowerCase() : path.normalize(value);

export function validatePrewarmOptions(input) {
  if (!path.isAbsolute(input.vaultRoot ?? '')) throw new TypeError('vaultRoot must be absolute');
  if (!path.isAbsolute(input.homeRoot ?? '')) throw new TypeError('homeRoot must be absolute');
  if (input.profilePath !== undefined && !path.isAbsolute(input.profilePath)) throw new TypeError('profilePath must be absolute');
  if (!duration.test(input.every ?? '')) throw new TypeError('every must be one positive OpenClaw duration such as 30m, 1h, or 1d');
}

export function prewarmDeclarationKey(input) {
  validatePrewarmOptions(input);
  const scope = JSON.stringify([normalized(input.vaultRoot),normalized(input.homeRoot),input.profilePath ? normalized(input.profilePath) : null]);
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
    ...(input.profilePath ? ['--profile-path',input.profilePath] : []),
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
