# Code Map: `adapters`
[Up: daily_tasks](../CODE_MAP.md)

## 1. Upward Ingress
Immediate caller and integration context:
* **Caller**: [`../auth/gmail.py`](../auth/gmail.py) -> `gmail`
* **Caller**: [`../server/harness_message_intake.py`](../server/harness_message_intake.py) -> `harness_message_intake`
* **Caller**: [`../server/markdown_workspace_reader.py`](../server/markdown_workspace_reader.py) -> `markdown_workspace_reader`

---

## 2. Local Interface & Public Surface
* **Responsibility**: Group the port adapter implementations.
* **Ubiquitous Language Concepts**: [`Daily Plan`](../../../docs/GLOSSARY.md), [`Milestone`](../../../docs/GLOSSARY.md), [`Project`](../../../docs/GLOSSARY.md), [`Task`](../../../docs/GLOSSARY.md)

```text
__init__.py
`-- (no public symbols)

markdown_daily_plan_adapter.py
`-- class MarkdownDailyPlanAdapter
    |-- def __init__(self, root: Path, name: str) -> None
    `-- def fetch_plans(self, around: date) -> Result[tuple[DailyPlan, ...]]

markdown_project_plan_adapter.py
`-- class MarkdownProjectPlanAdapter
    |-- def __init__(self, root: Path, name: str) -> None
    `-- def fetch_projects(self) -> Result[ProjectPlanSnapshot]

markdown_record_files.py
|-- SKIPPED_DIRECTORIES: Final
`-- def markdown_record_files(root: Path) -> tuple[PurePosixPath, ...]

markdown_record_kind.py
`-- def markdown_record_kind(path: PurePosixPath) -> MarkdownRecordKind | None
```

---

## 3. Sub-Packages (1 Tier Down)
| Sub-Directory | Responsibility | Map Link |
| :--- | :--- | :--- |
| `communication/` | Group the read-only communication source adapters. | [communication/CODE_MAP.md](communication/CODE_MAP.md) |
