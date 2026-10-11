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
  if (profile?.schema_version === 2) return validatePreferenceLayer(profile);
  return validateEffectiveProfile(profile);
}

export function validatePreferenceLayer(profile, scope) {
  const errors = [];
  const object = value => value && typeof value === 'object' && !Array.isArray(value);
  if (!object(profile) || profile.schema_version !== 2) return {valid:false,errors:['schema_version must be 2']};
  for (const key of Object.keys(profile)) if (!['schema_version','user','timezone','priorities','templates','projectIndex','vaultRoot','projectsRoot','dailyPlansRelative'].includes(key)) errors.push(`unknown preference: ${key}`);
  if (Object.hasOwn(profile,'user')) {
    if (!object(profile.user)) errors.push('user must be an object');
    else for (const [key,value] of Object.entries(profile.user)) {
      if (!['name','email'].includes(key) || typeof value !== 'string' || !value.trim() || (key === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value))) errors.push(`invalid user.${key}`);
    }
  }
  if (Object.hasOwn(profile,'timezone') && profile.timezone !== null) {
    try { resolveTimezone(profile.timezone); } catch (error) { errors.push(`valid IANA timezone or system required: ${error.message}`); }
  }
  if (Object.hasOwn(profile,'priorities') && profile.priorities !== null && (!Array.isArray(profile.priorities) || profile.priorities.some(value => typeof value !== 'string' || !value.trim()))) errors.push('priorities must be explicit text entries');
  if (Object.hasOwn(profile,'templates')) {
    if (!object(profile.templates)) errors.push('templates must be an object');
    else for (const [key,value] of Object.entries(profile.templates)) if (!['projectIndex','dailyPlan','milestone','task','planDayReview'].includes(key) || (value !== null && (!validStoredPath(value) || !/\.md$/i.test(value)))) errors.push(`invalid templates.${key}`);
  }
  if (Object.hasOwn(profile,'projectIndex') && (!object(profile.projectIndex) || Object.keys(profile.projectIndex).some(key => key !== 'ttlSeconds') || (Object.hasOwn(profile.projectIndex,'ttlSeconds') && profile.projectIndex.ttlSeconds !== null && (!Number.isSafeInteger(profile.projectIndex.ttlSeconds) || profile.projectIndex.ttlSeconds < 0)))) errors.push('projectIndex.ttlSeconds must be a nonnegative integer or null');
  for (const key of ['vaultRoot','projectsRoot','dailyPlansRelative']) if (Object.hasOwn(profile,key)) {
    if (scope === 'user') errors.push(`${key} is a project binding, not a user preference`);
    if (key !== 'dailyPlansRelative' && !validStoredPath(profile[key])) errors.push(`invalid ${key}`);
    if (key === 'dailyPlansRelative' && (typeof profile[key] !== 'string' || !profile[key] || path.isAbsolute(profile[key]) || profile[key].split(/[\\/]/).some(part => part === '..' || part === '.' || !part))) errors.push('dailyPlansRelative must stay beneath vaultRoot');
  }
  let resolvedTimezone;
  try { resolvedTimezone = resolveTimezone(profile.timezone ?? 'system'); } catch { /* The validation above retains the diagnostic. */ }
  return {valid:errors.length === 0,errors,...(resolvedTimezone ? {resolvedTimezone} : {})};
}

export function validateEffectiveProfile(profile) {
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
