# Responsibility: Build the relation and lookup layer of the state graph.
# Public interface:
# `-- build_index(records, relations, tree, settings)
"""Parent links, two-way relations, path/person/term lookups and file hashes, keyed by record id."""

from collections.abc import Iterable
from uuid import UUID

from daily_tasks.domain import Blocker, Milestone, PersonIndex, Project, ProjectTree, StateGraphIndex, Task
from daily_tasks.graph.title_terms import title_terms
from daily_tasks.graph.types import GraphRecords, RecordRelations, StateGraphSettings


def build_index(
    records: GraphRecords, relations: RecordRelations, tree: tuple[ProjectTree, ...], settings: StateGraphSettings
) -> StateGraphIndex:
    """Return lookups in tree order; daily plan paths and content hashes join `settings.file_hashes`."""
    ordered = _tree_order(records, tree)
    known = {record.id for record in ordered}
    file_hashes = dict(settings.file_hashes)
    for plan in records.plans.values():
        file_hashes.setdefault(plan.path, plan.content_hash)
    return StateGraphIndex(
        project_order=tuple(node.project_id for node in tree),
        parent=_parents(ordered),
        depends_on=relations.depends_on,
        required_by=relations.required_by,
        blocked_by=relations.blocked_by,
        blocks=relations.blocks,
        by_path={record.path: record.id for record in ordered},
        by_person=_by_person(ordered),
        origin_by_record={key: value for key, value in settings.origin_by_record.items() if key in known},
        title_terms=_title_terms(ordered),
        threads=dict(settings.threads),
        file_hashes=file_hashes,
    )


type _Record = Project | Milestone | Task | Blocker


def _tree_order(records: GraphRecords, tree: tuple[ProjectTree, ...]) -> list[_Record]:
    ordered: list[_Record] = []
    for project_node in tree:
        ordered.append(records.projects[project_node.project_id])
        for milestone_node in project_node.milestones:
            ordered.append(records.milestones[milestone_node.milestone_id])
            ordered.extend(records.tasks[task_id] for task_id in milestone_node.task_ids)
        ordered.extend(records.blockers[blocker_id] for blocker_id in project_node.blocker_ids)
    return ordered


def _parents(ordered: Iterable[_Record]) -> dict[UUID, UUID]:
    parents: dict[UUID, UUID] = {}
    for record in ordered:
        if isinstance(record, Task):
            parents[record.id] = record.milestone_id
        elif isinstance(record, Milestone | Blocker):
            parents[record.id] = record.project_id
    return parents


def _by_person(ordered: Iterable[_Record]) -> dict[str, PersonIndex]:
    """Owners of projects, tasks and blockers, and effective assignees of tasks (assignee, else owner)."""
    owns: dict[str, list[UUID]] = {}
    assigned: dict[str, list[UUID]] = {}
    for record in ordered:
        if isinstance(record, Milestone):
            continue
        owns.setdefault(record.owner, []).append(record.id)
        if isinstance(record, Task):
            assigned.setdefault(record.assignee or record.owner, []).append(record.id)
    people = dict.fromkeys([*owns, *assigned])
    return {
        person: PersonIndex(owns=tuple(owns.get(person, ())), assigned=tuple(assigned.get(person, ())))
        for person in people
    }


def _title_terms(ordered: Iterable[_Record]) -> dict[str, tuple[UUID, ...]]:
    terms: dict[str, list[UUID]] = {}
    for record in ordered:
        for term in title_terms(record.title):
            terms.setdefault(term, []).append(record.id)
    return {term: tuple(ids) for term, ids in terms.items()}
