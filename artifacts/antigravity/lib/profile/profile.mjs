import path from 'node:path';

export function validateProfile(profile) {
  const errors = [];
  if (profile?.schema_version !== 1) errors.push('schema_version must be 1');
  if (!profile?.user?.name || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(profile?.user?.email || '')) errors.push('user name and email required');
  try {
    if (typeof profile?.timezone !== 'string' || !profile.timezone) throw new Error();
    new Intl.DateTimeFormat('en', { timeZone: profile.timezone }).format();
  } catch { errors.push('valid IANA timezone required'); }
  if (!Array.isArray(profile?.priorities) || profile.priorities.some(p => typeof p !== 'string' || !p.trim())) errors.push('priorities must be explicit text entries');
  for (const key of ['vaultRoot', 'projectsRoot']) if (typeof profile?.[key] !== 'string' || !path.isAbsolute(profile[key])) errors.push(`${key} must be absolute`);
  const relative = profile?.dailyPlansRelative;
  if (typeof relative !== 'string' || !relative || path.isAbsolute(relative) || relative.split(/[\\/]/).some(part => part === '..' || part === '.' || !part)) errors.push('dailyPlansRelative must stay beneath vaultRoot');
  return { valid: errors.length === 0, errors };
}
