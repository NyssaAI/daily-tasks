"""Responsibility: Fingerprint the record inventory a state graph was built from.
Public interface:
`-- inventory_hash(records, file_hashes)

Stable SHA-256 over record ids, update times and file content hashes.
"""

import hashlib
from collections.abc import Mapping

from daily_tasks.graph.types import GraphRecords


def inventory_hash(records: GraphRecords, file_hashes: Mapping[str, str]) -> str:
    """Return `sha256:<hex>`; independent of source and record order, changed by any record or file edit."""
    lines = [
        *(f"record {r.id} {r.updated_at.isoformat()}" for r in records.projects.values()),
        *(f"record {r.id} {r.updated_at.isoformat()}" for r in records.milestones.values()),
        *(f"record {r.id} {r.updated_at.isoformat()}" for r in records.tasks.values()),
        *(f"record {r.id} {r.updated_at.isoformat()}" for r in records.blockers.values()),
        *(f"plan {p.id} {p.content_hash}" for p in records.plans.values()),
        *(f"file {path} {digest}" for path, digest in file_hashes.items()),
    ]
    digest = hashlib.sha256("\n".join(sorted(lines)).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"
