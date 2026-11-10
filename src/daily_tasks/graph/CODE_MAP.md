# Code Map: `graph`
[Up: daily_tasks](../CODE_MAP.md)

## 1. Upward Ingress
Immediate caller and integration context:
* **Caller**: [`../domain/state_graph_context.py`](../domain/state_graph_context.py) -> `state_graph_context`
* **Caller**: [`../domain/__init__.py`](../domain/__init__.py) -> `__init__`
* **Caller**: [`../matching/__init__.py`](../matching/__init__.py) -> `__init__`

---

## 2. Local Interface & Public Surface
* **Responsibility**: Expose the state graph build boundary API.
* **Ubiquitous Language Concepts**: [`Daily Plan`](../../../docs/GLOSSARY.md), [`Milestone`](../../../docs/GLOSSARY.md), [`Project`](../../../docs/GLOSSARY.md), [`Task`](../../../docs/GLOSSARY.md)

```text
__init__.py
`-- (no public symbols)

build_index.py
`-- def build_index( records: GraphRecords, relations: RecordRelations, tree: tuple[ProjectTree, ...], settings: StateGraphSettings ) -> StateGraphIndex

build_record_nodes.py
`-- def build_record_nodes(records: GraphRecords) -> StateGraphRecords

build_state_graph.py
`-- def build_state_graph( project_reads: Sequence[ProjectPlanSourceRead], plan_reads: Sequence[DailyPlanSourceRead], settings: StateGraphSettings, built_at: datetime, ) -> Result[StateGraph]

build_tree.py
`-- def build_tree(records: GraphRecords) -> tuple[tuple[ProjectTree, ...], tuple[Diagnostic, ...]]

derive_blocker_facts.py
`-- def derive_blocker_facts(records: GraphRecords, local_date: date) -> dict[UUID, BlockerFacts]

derive_milestone_facts.py
`-- def derive_milestone_facts( records: GraphRecords, relations: RecordRelations, tree: tuple[ProjectTree, ...] ) -> dict[UUID, MilestoneFacts]

derive_rollover.py
`-- def derive_rollover(records: GraphRecords, local_date: date) -> Rollover

derive_summary.py
`-- def derive_summary( records: GraphRecords, task_facts: Mapping[UUID, TaskFacts], today: Today, rollover: Rollover, settings: StateGraphSettings, ) -> StateGraphSummary

derive_task_facts.py
`-- def derive_task_facts( records: GraphRecords, relations: RecordRelations, plannable_milestones: Set[UUID], user_email: str, local_date: date, ) -> dict[UUID, TaskFacts]

derive_today.py
`-- def derive_today(records: GraphRecords, task_facts: Mapping[UUID, TaskFacts], local_date: date) -> Today

format_dod_progress.py
|-- def dod_ratio(progress: DodProgress) -> float
`-- def format_dod_progress(progress: DodProgress) -> str

inventory_hash.py
`-- def inventory_hash(records: GraphRecords, file_hashes: Mapping[str, str]) -> str

is_terminal_state.py
`-- def is_terminal_state(state: str) -> bool

local_date_in.py
`-- def local_date_in(instant: datetime, timezone: str) -> Result[date]

merge_records.py
`-- def merge_records( snapshots: Sequence[ProjectPlanSnapshot], plans: Sequence[DailyPlan] ) -> tuple[GraphRecords, tuple[Diagnostic, ...]]

milestone_completion_percent.py
`-- def milestone_completion_percent(facts: MilestoneFacts) -> float

planned_days.py
`-- def planned_days(plans: Mapping[date, DailyPlan], local_date: date) -> dict[UUID, tuple[date, date | None]]

resolve_relations.py
`-- def resolve_relations(records: GraphRecords) -> RecordRelations

state_graph_builder.py
`-- class StateGraphBuilder
    |-- def __init__( self, project_ports: Sequence[ProjectPlanPort], plan_ports: Sequence[DailyPlanPort], settings: StateGraphSettings, clock: Callable[[], datetime], ) -> None
    `-- def build(self) -> Result[StateGraph]

title_terms.py
`-- def title_terms(title: str) -> tuple[str, ...]

types.py
|-- class DailyPlanSourceRead
|-- class GraphRecords
|-- class ProjectPlanSourceRead
|-- class RecordRelations
`-- class StateGraphSettings
```

---

## 3. Sub-Packages (1 Tier Down)
*None (leaf module directory).*
