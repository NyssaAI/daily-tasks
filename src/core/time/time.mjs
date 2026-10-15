/** Strict GMT input: no locale parsing, offsets, impossible dates or normalization. */
export function utcTimestamp(value) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?Z$/.test(value)) {
    throw new TypeError('Expected an ISO 8601 GMT timestamp ending in Z');
  }
  const date = new Date(value);
  if (!Number.isFinite(date.getTime())) throw new TypeError('Invalid GMT timestamp');
  const normalized = date.toISOString();
  if (normalized.slice(0, 19) !== value.slice(0, 19)) throw new TypeError('Impossible GMT date or time');
  return normalized;
}

export function activityTime(reported, now = new Date().toISOString()) {
  const recorded_at = utcTimestamp(now);
  if (reported != null && typeof reported !== 'string') throw new TypeError('Reported time must be a string');
  const value = reported?.trim();
  // An apparent precise timestamp must validate; prose is explicitly approximate.
  const precise = value && (/^\d{4}[-/]/.test(value) || /\d{2}:\d{2}:\d{2}/.test(value));
  return {activity_at: precise ? utcTimestamp(value) : recorded_at,
    recorded_at, time_defaulted: !precise};
}

export function resolveTimezone(timezone) {
  if (typeof timezone !== 'string' || !timezone.trim()) throw new TypeError('IANA timezone or system is required');
  const resolved = timezone === 'system' ? Intl.DateTimeFormat().resolvedOptions().timeZone : timezone;
  if (typeof resolved !== 'string' || !resolved.trim()) throw new Error('System timezone detection failed; specify an IANA timezone');
  new Intl.DateTimeFormat('en-US', {timeZone: resolved});
  return resolved;
}

function formatter(timezone, options) {
  return new Intl.DateTimeFormat('en-US', {timeZone: resolveTimezone(timezone), ...options});
}

export function localDay(iso, timezone) {
  const parts = formatter(timezone, {year:'numeric', month:'2-digit', day:'2-digit'})
    .formatToParts(new Date(utcTimestamp(iso)));
  const values = Object.fromEntries(parts.map(part => [part.type, part.value]));
  return `${values.year}.${values.month}.${values.day}`;
}

export function displayTime(iso, timezone) {
  timezone = resolveTimezone(timezone);
  const text = formatter(timezone, {year:'numeric', month:'short', day:'numeric',
    hour:'numeric', minute:'2-digit', second:'2-digit', timeZoneName:'short'})
    .format(new Date(utcTimestamp(iso)));
  return `${text} (${timezone})`;
}
