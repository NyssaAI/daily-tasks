# Code Map: `session`
[Up: daily_tasks](../CODE_MAP.md)

## 1. Upward Ingress
Immediate caller and integration context:
* **Caller**: [`../server/live_session.py`](../server/live_session.py) -> `live_session`
* **Caller**: [`../server/planning_tools.py`](../server/planning_tools.py) -> `planning_tools`
* **Caller**: [`../server/tool_reply.py`](../server/tool_reply.py) -> `tool_reply`

---

## 2. Local Interface & Public Surface
* **Responsibility**: Expose the planning session lifecycle, row resolution, screen rendering and adjudication.
* **Ubiquitous Language Concepts**: [`Daily Plan`](../../../docs/GLOSSARY.md), [`Decision Log`](../../../docs/GLOSSARY.md), [`Milestone`](../../../docs/GLOSSARY.md), [`Planning Session`](../../../docs/GLOSSARY.md), [`Project`](../../../docs/GLOSSARY.md), [`Record Change`](../../../docs/GLOSSARY.md), [`Suggestion`](../../../docs/GLOSSARY.md), [`Task`](../../../docs/GLOSSARY.md)

```text
__init__.py
`-- (no public symbols)

add_suggestions.py
`-- def add_suggestions(state: SessionState, suggestions: tuple[Suggestion, ...], now: datetime) -> Result[SessionState]

adjudicate_suggestions.py
`-- def adjudicate_suggestions( suggestions: Suggestions, verdicts: Sequence[AdjudicationVerdict], graph: StateGraph, actor: Actor, session_id: UUID, now: datetime, new_id: Callable[[], UUID], ) -> Result[Adjudication]

adjudication.py
`-- class Adjudication

adjudication_effect.py
`-- def adjudication_effect( graph: StateGraph, suggestion: Suggestion, proposed: Mapping[str, JsonValue], context: OperationContext ) -> Result[OperationStep]

adjudication_verdict.py
`-- class AdjudicationVerdict

apply_operation.py
`-- def apply_operation(graph: StateGraph, operation: Operation, context: OperationContext) -> Result[OperationStep]

apply_operations.py
`-- def apply_operations( graph: StateGraph, operations: Operations, new_id: Callable[[], UUID], now: datetime ) -> Result[OperationOutcome]

assign_days_refs.py
`-- def assign_days_refs(graph: StateGraph, project_id: UUID, include_in_progress: bool) -> tuple[RowRef, ...]

build_daily_plan_document.py
`-- def build_daily_plan_document( state: SessionState, decisions: Sequence[DecisionLogEntry], existing: DailyPlan | None, blockers: Mapping[UUID, Blocker], projects_prefix: str, plan_id: UUID, now: datetime, ) -> DailyPlanDocument

cancel_session.py
`-- def cancel_session(state: SessionState, now: datetime) -> Result[SessionState]

confirm_plan.py
`-- class ConfirmPlan
    |-- def __init__(self, store: LocalFileStore) -> None
    `-- def confirm( self, changes: Sequence[RecordChange], document: DailyPlanDocument, confirmed_by_user: bool ) -> Result[str]

confirm_refs.py
`-- def confirm_refs(graph: StateGraph) -> tuple[RowRef, ...]

confirm_session.py
`-- def confirm_session(state: SessionState, now: datetime) -> Result[SessionState]

decision_entry.py
`-- def decision_entry( context: OperationContext, action: str, question: str, decision: str, record_ids: tuple[UUID, ...], before: Mapping[str, JsonValue] | None, after: Mapping[str, JsonValue] | None, ) -> DecisionLogEntry

decision_logger.py
`-- class DecisionLogger
    |-- def __init__(self, store: LocalFileStore) -> None
    `-- def append(self, entries: Sequence[DecisionLogEntry]) -> Result[int]

finish_assign_days.py
`-- def finish_assign_days(state: SessionState, now: datetime) -> Result[SessionState]

format_day.py
`-- def format_day(day: date | None) -> str

markdown_table.py
`-- def markdown_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str

next_project.py
`-- def next_project(state: SessionState, now: datetime) -> Result[SessionState]

number_screen.py
`-- def number_screen( session: PlanningSession, key: str, kind: Literal["plan-the-day", "assign-days", "confirm"], refs: Sequence[RowRef], now: datetime, ) -> PlanningSession

open_task.py
`-- def open_task(graph: StateGraph, task_id: UUID) -> bool

operation_context.py
`-- class OperationContext

operation_outcome.py
`-- class OperationOutcome

operation_planned_for.py
`-- def operation_planned_for( graph: StateGraph, item_type: ItemType, item_id: UUID, local_date: date | None ) -> Result[tuple[StateGraph, date | None]]

operation_record_change.py
`-- def operation_record_change( graph: StateGraph, context: OperationContext, record_type: Literal["project", "milestone", "task", "blocker"], record_id: UUID, before: Mapping[str, JsonValue] | None, after: Mapping[str, JsonValue], ) -> RecordChange

operation_set_state.py
`-- def operation_set_state( graph: StateGraph, record_type: Literal["task", "blocker", "milestone", "project"], record_id: UUID, state: str ) -> StateGraph

operation_status_rule.py
|-- ALLOWED_STATES: Final[Mapping[str, frozenset[str]]]
`-- def operation_status_rule(graph: StateGraph, operation: SetStatus) -> Result[str]

operation_step.py
`-- class OperationStep

parse_verdicts.py
`-- def parse_verdicts( session: PlanningSession, verdicts: Sequence[Mapping[str, JsonValue]], original_words: str ) -> Result[tuple[AdjudicationVerdict, ...]]

plan_the_day_refs.py
`-- def plan_the_day_refs( graph: StateGraph, previous_plan: DailyPlan | None, suggestions: tuple[Suggestion, ...] ) -> tuple[RowRef, ...]

refresh_today.py
`-- def refresh_today(graph: StateGraph) -> StateGraph

render_assign_days.py
`-- def render_assign_days(state: SessionState) -> str

render_confirm_plan.py
`-- def render_confirm_plan(state: SessionState) -> str

render_plan_the_day.py
`-- def render_plan_the_day(state: SessionState) -> str

require_stage.py
`-- def require_stage( state: SessionState, allowed: Collection[SessionStage], attempted: str, expected_next: str | None = None ) -> Result[SessionState]

resolve_row.py
`-- def resolve_row(session: PlanningSession, reference: str) -> Result[RowRef]

review_projects.py
`-- def review_projects(state: SessionState, now: datetime) -> Result[SessionState]

screen_rows.py
`-- def screen_rows(session: PlanningSession, key: str) -> tuple[tuple[int, RowRef], ...]

session_stage.py
`-- class SessionStage(StrEnum)

session_state.py
`-- class SessionState
    `-- def with_session(self, session: PlanningSession, stage: SessionStage) -> "SessionState"

show_confirm.py
`-- def show_confirm(state: SessionState, now: datetime) -> SessionState

show_project.py
`-- def show_project(state: SessionState, project_id: UUID, now: datetime) -> SessionState

start_session.py
`-- def start_session(state: SessionState, previous_plan: DailyPlan | None, now: datetime) -> Result[SessionState]

status_mark.py
`-- def status_mark(state: str) -> str
```

---

## 3. Sub-Packages (1 Tier Down)
*None (leaf module directory).*
