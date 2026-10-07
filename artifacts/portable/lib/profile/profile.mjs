import path from 'node:path';
import { resolveTimezone } from '../time/time.mjs';

export function validStoredPath(value) {
  return typeof value === 'string' && !!value &&
    (path.isAbsolute(value) || value === '.' || value === '~' || /^(\.\/|~\/)/.test(value)) &&
    !value.split(/[\\/]/).includes('..');
}

export function expandStoredPath(value, vaultRoot, homeRoot) {
  if (!validStoredPath(value)) throw new TypeError('Expected an absolute, ./ vault-relative or ~/ home-relative path without traversal');
  if (value === '~' || value.startsWith('~/')) return path.resolve(homeRoot,value.slice(2));
  return path.isAbsolute(value) ? path.normalize(value) : path.resolve(vaultRoot,value);
}

export function validateProfile(profile) {
  const errors = [];
  if (profile?.schema_version !== 1) errors.push('schema_version must be 1');
  if (!profile?.user?.name || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(profile?.user?.email || '')) errors.push('user name and email required');
  let resolvedTimezone;
  try { resolvedTimezone = resolveTimezone(profile?.timezone); }
  catch (error) { errors.push(`valid IANA timezone or system required: ${error.message}`); }
  if (!Array.isArray(profile?.priorities) || profile.priorities.some(p => typeof p !== 'string' || !p.trim())) errors.push('priorities must be explicit text entries');
  for (const key of ['vaultRoot', 'projectsRoot']) if (!validStoredPath(profile?.[key])) errors.push(`${key} must be absolute, ./ vault-relative or ~/ home-relative`);
  const relative = profile?.dailyPlansRelative;
  if (typeof relative !== 'string' || !relative || path.isAbsolute(relative) || relative.split(/[\\/]/).some(part => part === '..' || part === '.' || !part)) errors.push('dailyPlansRelative must stay beneath vaultRoot');
  if (Object.hasOwn(profile ?? {}, 'templates')) {
    const templates = profile.templates;
    if (!templates || typeof templates !== 'object' || Array.isArray(templates)) errors.push('templates must be an object');
    else for (const [key, filename] of Object.entries(templates)) {
      if (!['projectIndex', 'dailyPlan', 'milestone', 'task','planDayReview'].includes(key)) errors.push(`unknown template: ${key}`);
      else if (!validStoredPath(filename) || !/\.md$/i.test(filename)) errors.push(`templates.${key} must be a portable Markdown file path`);
    }
  }
  if (Object.hasOwn(profile ?? {},'projectIndex') && (!profile.projectIndex || Array.isArray(profile.projectIndex) ||
      !Number.isSafeInteger(profile.projectIndex.ttlSeconds) || profile.projectIndex.ttlSeconds < 0 ||
      Object.keys(profile.projectIndex).some(key => key !== 'ttlSeconds'))) errors.push('projectIndex.ttlSeconds must be a nonnegative integer');
  return { valid: errors.length === 0, errors, ...(resolvedTimezone ? {resolvedTimezone} : {}) };
}
