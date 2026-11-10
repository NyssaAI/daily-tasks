# Code Map: `ports`
[Up: daily_tasks](../CODE_MAP.md)

## 1. Upward Ingress
Immediate caller and integration context:
* **Caller**: [`../adapters/markdown_daily_plan_adapter.py`](../adapters/markdown_daily_plan_adapter.py) -> `markdown_daily_plan_adapter`
* **Caller**: [`../adapters/markdown_project_plan_adapter.py`](../adapters/markdown_project_plan_adapter.py) -> `markdown_project_plan_adapter`
* **Caller**: [`../adapters/communication/communication_multiplexer.py`](../adapters/communication/communication_multiplexer.py) -> `communication_multiplexer`

---

## 2. Local Interface & Public Surface
* **Responsibility**: Expose the runtime port contracts the planning session reads and writes through.
* **Ubiquitous Language Concepts**: [`Daily Plan`](../../../docs/GLOSSARY.md), [`Milestone`](../../../docs/GLOSSARY.md), [`Planning Session`](../../../docs/GLOSSARY.md), [`Project`](../../../docs/GLOSSARY.md), [`Task`](../../../docs/GLOSSARY.md)

```text
__init__.py
`-- (no public symbols)

communication_port.py
`-- class CommunicationPort(Protocol)
    `-- def fetch_new_messages(self, since: FetchCursors) -> Result[FetchBatch]

daily_plan_port.py
`-- class DailyPlanPort(Protocol)
    `-- def fetch_plans(self, around: date) -> Result[tuple[DailyPlan, ...]]

local_file_store.py
`-- class LocalFileStore(Protocol)
    |-- def apply(self, changes: Sequence[RecordChange]) -> Result[tuple[RecordChange, ...]]
    |-- def write_daily_plan(self, document: DailyPlanDocument) -> Result[str]
    |-- def save_suggestions(self, suggestions: Suggestions) -> Result[None]
    |-- def append_decisions(self, entries: Sequence[DecisionLogEntry]) -> Result[None]
    `-- def save_session(self, session: PlanningSession) -> Result[None]

project_plan_port.py
`-- class ProjectPlanPort(Protocol)
    `-- def fetch_projects(self) -> Result[ProjectPlanSnapshot]

types.py
|-- class FetchBatch
|-- class MalformedRecord
`-- class ProjectPlanSnapshot
```

---

## 3. Sub-Packages (1 Tier Down)
*None (leaf module directory).*
