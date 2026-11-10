# Code Map: `storage`
[Up: daily_tasks](../CODE_MAP.md)

## 1. Upward Ingress
Immediate caller and integration context:
* **Caller**: [`../adapters/markdown_daily_plan_adapter.py`](../adapters/markdown_daily_plan_adapter.py) -> `markdown_daily_plan_adapter`
* **Caller**: [`../adapters/markdown_project_plan_adapter.py`](../adapters/markdown_project_plan_adapter.py) -> `markdown_project_plan_adapter`
* **Caller**: [`../ports/local_file_store.py`](../ports/local_file_store.py) -> `local_file_store`

---

## 2. Local Interface & Public Surface
* **Responsibility**: Group the Markdown record storage features.
* **Ubiquitous Language Concepts**: [`Record Change`](../../../docs/GLOSSARY.md), [`Workspace`](../../../docs/GLOSSARY.md)

```text
__init__.py
`-- (no public symbols)

apply_record_change.py
|-- FRONTMATTER_KEYS: Final[frozenset[str]]
`-- def apply_record_change(text: str, change: RecordChange) -> Result[str, ParseError]

atomic_write.py
`-- def atomic_write(path: Path, data: bytes) -> None

cursor_store.py
`-- class CursorStore
    |-- def __init__(self, state_root: Path, workspace_root: str) -> None
    |-- def load(self) -> Result[FetchCursors]
    `-- def save(self, cursors: FetchCursors) -> Result[None]

markdown_file_store.py
`-- class MarkdownFileStore
    |-- def __init__( self, workspace_root: Path, clock: Callable[[], datetime], records_root: Path = Path("projects"), daily_plans_root: Path = Path("daily-plans"), state_root: Path = Path(".nyssa-ai/daily-tasks"), ) -> None
    |-- def apply(self, changes: Sequence[RecordChange]) -> Result[tuple[RecordChange, ...]]
    |-- def write_daily_plan(self, document: DailyPlanDocument) -> Result[str]
    |-- def save_suggestions(self, suggestions: Suggestions) -> Result[None]
    |-- def append_decisions(self, entries: Sequence[DecisionLogEntry]) -> Result[None]
    `-- def save_session(self, session: PlanningSession) -> Result[None]
```

---

## 3. Sub-Packages (1 Tier Down)
| Sub-Directory | Responsibility | Map Link |
| :--- | :--- | :--- |
| `cst/` | Expose the Markdown CST parse, edit and render boundary API. | [cst/CODE_MAP.md](cst/CODE_MAP.md) |
