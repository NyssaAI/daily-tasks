"""Responsibility: Compute planning facts for every blocker.
Public interface:
`-- derive_blocker_facts(records, local_date)

Planned day, owner and state per blocker.
"""

from datetime import date
from uuid import UUID

from daily_tasks.domain import BlockerFacts
from daily_tasks.graph.planned_days import planned_days
from daily_tasks.graph.types import GraphRecords


def derive_blocker_facts(records: GraphRecords, local_date: date) -> dict[UUID, BlockerFacts]:
    """Return facts keyed by blocker id; `planned_for` is the earliest plan on or after `local_date`."""
    planned = planned_days(records.plans, local_date)
    return {
        blocker_id: BlockerFacts(
            planned_for=planned[blocker_id][0] if blocker_id in planned else None,
            owner=blocker.owner,
            state=blocker.state,
        )
        for blocker_id, blocker in records.blockers.items()
    }
