import path from 'node:path';
import { diagnostic } from './validation.mjs';
import { isUuid7 } from '../identity/identity.mjs';

const style = value => /^[a-z]:[\\/]/i.test(value || '') ? path.win32 : path.posix;
const comparable = value => style(value) === path.win32 ? value.toLowerCase().replaceAll('\\','/') : value;

/** Check backlinks and propose navigational repairs; never write Markdown. */
export function checkLinks(records) {
  const diagnostics = [];
  const index = new Map();
  for (const record of records) if (isUuid7(record.id)) index.set(record.id,[...(index.get(record.id) || []),record]);
  const inverse = {blocked_by:'blocks',blocks:'blocked_by',depends_on:'required_by',required_by:'depends_on'};
  for (const record of records) {
    for (const reference of record.refs || []) {
      if (!isUuid7(reference?.id)) continue; // Identity validation owns this diagnostic.
      const targets = index.get(reference.id) || [];
      if (targets.length !== 1) {
        diagnostics.push(diagnostic(record,targets.length ? 'duplicate-reference' : 'missing-reference',`Cannot resolve reference ${reference.id}`));
        continue;
      }
      const target = targets[0];
      if (!record.path || !target.path || typeof reference.target !== 'string') {
        diagnostics.push(diagnostic(record,'unverifiable-path','Source and target paths are needed to validate a wiki link'));
        continue;
      }
      const paths = style(record.path);
      const linkedFile = reference.target.split('#')[0];
      const linkWithExtension = /\.md$/i.test(linkedFile) ? linkedFile : `${linkedFile}.md`;
      const resolved = paths.resolve(paths.dirname(record.path),linkWithExtension);
      if (comparable(resolved) !== comparable(paths.resolve(target.path))) {
        const proposedTarget = paths.relative(paths.dirname(record.path),target.path).replaceAll('\\','/').replace(/\.md$/i,'');
        diagnostics.push(diagnostic(record,'path-mismatch',`Wiki link does not match UUID ${reference.id}`, {referenceId:reference.id,proposedTarget}));
      }
    }
    for (const [relation,backlink] of Object.entries(inverse)) {
      for (const targetId of record[relation] || []) {
        if (!isUuid7(targetId)) continue;
        const targets = index.get(targetId) || [];
        if (targets.length !== 1) {
          diagnostics.push(diagnostic(record,targets.length ? 'duplicate-reference' : 'missing-reference',`Cannot resolve ${relation} ${targetId}`));
          continue;
        }
        if (!targets[0][backlink]?.includes(record.id)) diagnostics.push(diagnostic(record,'missing-backlink',`${targetId} needs ${backlink} reference to ${record.id}`, {referenceId:targetId,relation:backlink}));
        if (relation === 'depends_on' && targets[0].state === 'cancelled') diagnostics.push(diagnostic(record,'cancelled-prerequisite',`Prerequisite ${targetId} was cancelled; dependency remains informational`));
      }
    }
  }
  return diagnostics;
}
