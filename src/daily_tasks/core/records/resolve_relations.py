"""Responsibility: Resolve dependency and blocker references into two-way relation maps.
Public interface:
`-- resolve_relations(records)

Relations declared on either side are merged; references to unknown records become diagnostics.
"""

from collections.abc import Iterable, Mapping
from uuid import UUID

from daily_tasks.core.records.diagnostic import Diagnostic
from daily_tasks.core.records.types import GraphRecords, RecordRelations


def resolve_relations(records: GraphRecords) -> RecordRelations:
    """Return depends_on/required_by between tasks and blocked_by/blocks between records and blockers.

    A task's `depends_on` and the other task's `required_by` describe the same edge, as do a record's
    `blocked_by` and the blocker's `blocks`; each edge appears once, in source order.
    """
    known = {*records.projects, *records.milestones, *records.tasks, *records.blockers}
    diagnostics: list[Diagnostic] = []
    dependencies: list[tuple[UUID, UUID]] = []
    blockings: list[tuple[UUID, UUID]] = []
    for task in records.tasks.values():
        dependencies += _edges(task.id, task.depends_on, task.path, set(records.tasks), diagnostics, forward=True)
        dependencies += _edges(task.id, task.required_by, task.path, set(records.tasks), diagnostics, forward=False)
        blockings += _edges(task.id, task.blocked_by, task.path, set(records.blockers), diagnostics, forward=True)
    for milestone in records.milestones.values():
        blockings += _edges(
            milestone.id, milestone.blocked_by, milestone.path, set(records.blockers), diagnostics, forward=True
        )
    for blocker in records.blockers.values():
        blockings += _edges(blocker.id, blocker.blocks, blocker.path, known, diagnostics, forward=False)
    for plan in records.plans.values():
        for entry in plan.entries:
            if entry.item_id not in known:
                diagnostics.append(_unresolved(plan.path, entry.item_id))
    return RecordRelations(
        depends_on=_group(dependencies),
        required_by=_group((target, source) for source, target in dependencies),
        blocked_by=_group(blockings),
        blocks=_group((target, source) for source, target in blockings),
        diagnostics=tuple(diagnostics),
    )


def _edges(
    record_id: UUID,
    refs: Iterable[UUID],
    path: str,
    targets: set[UUID],
    diagnostics: list[Diagnostic],
    *,
    forward: bool,
) -> list[tuple[UUID, UUID]]:
    """Return (dependent, dependency) pairs; `forward=False` means `refs` point back at `record_id`."""
    edges: list[tuple[UUID, UUID]] = []
    for ref in refs:
        if ref not in targets:
            diagnostics.append(_unresolved(path, ref))
        else:
            edges.append((record_id, ref) if forward else (ref, record_id))
    return edges


def _group(edges: Iterable[tuple[UUID, UUID]]) -> Mapping[UUID, tuple[UUID, ...]]:
    grouped: dict[UUID, dict[UUID, None]] = {}
    for source, target in edges:
        grouped.setdefault(source, {})[target] = None
    return {source: tuple(targets) for source, targets in grouped.items()}


def _unresolved(path: str, ref: UUID) -> Diagnostic:
    return Diagnostic(level="warning", code="UNRESOLVED_REF", path=path, detail=f"ref {ref} not found in any project.")
