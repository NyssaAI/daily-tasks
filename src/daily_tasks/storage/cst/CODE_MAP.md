# Code Map: `cst`
[Up: storage](../CODE_MAP.md)

## 1. Upward Ingress
Immediate caller and integration context:
* **Caller**: [`../../adapters/markdown_daily_plan_adapter.py`](../../adapters/markdown_daily_plan_adapter.py) -> `markdown_daily_plan_adapter`
* **Caller**: [`../../adapters/markdown_project_plan_adapter.py`](../../adapters/markdown_project_plan_adapter.py) -> `markdown_project_plan_adapter`
* **Caller**: [`../../ports/local_file_store.py`](../../ports/local_file_store.py) -> `local_file_store`

---

## 2. Local Interface & Public Surface
* **Responsibility**: Expose the Markdown CST parse, edit and render boundary API.
* **Ubiquitous Language Concepts**: [`Daily Plan`](../../../../docs/GLOSSARY.md), [`Milestone`](../../../../docs/GLOSSARY.md), [`Project`](../../../../docs/GLOSSARY.md), [`Task`](../../../../docs/GLOSSARY.md)

```text
__init__.py
`-- (no public symbols)

append_decision.py
`-- def append_decision(document: MarkdownDocument, entry: str) -> Result[MarkdownDocument, ParseError]

checklist_item.py
`-- class ChecklistItem

frontmatter.py
`-- class Frontmatter

frontmatter_field.py
`-- class FrontmatterField

heading.py
`-- class Heading

line_ending.py
`-- def line_ending(document: MarkdownDocument) -> str

markdown_document.py
`-- class MarkdownDocument

parse_blocker.py
`-- def parse_blocker(document: MarkdownDocument, location: RecordLocation) -> Result[Blocker, ParseError]

parse_daily_plan.py
`-- def parse_daily_plan( document: MarkdownDocument, location: RecordLocation, base: DailyPlan | None = None ) -> Result[DailyPlanDocument, ParseError]

parse_error.py
`-- class ParseError

parse_frontmatter.py
|-- def format_scalar(value: ScalarValue, quoted: bool) -> str
`-- def parse_frontmatter(lines: tuple[SourceLine, ...]) -> Result[Frontmatter | None, ParseError]

parse_markdown.py
`-- def parse_markdown(text: str) -> Result[MarkdownDocument, ParseError]

parse_milestone.py
`-- def parse_milestone(document: MarkdownDocument, location: RecordLocation) -> Result[Milestone, ParseError]

parse_project.py
`-- def parse_project(document: MarkdownDocument, location: RecordLocation) -> Result[Project, ParseError]

parse_task.py
`-- def parse_task(document: MarkdownDocument, location: RecordLocation) -> Result[Task, ParseError]

read_blocker_row.py
`-- def read_blocker_row(row: TableRow) -> tuple[PlanBlockerView, tuple[int, ...]] | ParseError

read_item_row.py
`-- def read_item_row(row: TableRow) -> tuple[PlanItemView, bool] | ParseError

record_fields.py
|-- class RecordFields
|   |-- def definition_of_done(self) -> tuple[dict[str, object], ...]
|   |-- def frontmatter_values(self) -> dict[str, ScalarValue]
|   |-- def section(self, title: str) -> Section | None
|   |-- def section_refs(self, title: str) -> tuple[str, ...]
|   `-- def section_text(self, title: str) -> str | None
`-- WORK_MARKS: Final[Mapping[str, str]]

render_daily_plan.py
|-- SECTION_TITLES: Final[Mapping[str, str]]
`-- def render_daily_plan(document: DailyPlanDocument) -> str

reparse_lines.py
`-- def reparse_lines(lines: Sequence[SourceLine]) -> Result[MarkdownDocument, ParseError]

scalar_value.py
`-- (no public symbols)

section.py
`-- class Section

set_checklist_mark.py
`-- def set_checklist_mark(document: MarkdownDocument, item_id: str, mark: str) -> Result[MarkdownDocument, ParseError]

set_frontmatter_field.py
`-- def set_frontmatter_field( document: MarkdownDocument, key: str, value: ScalarValue ) -> Result[MarkdownDocument, ParseError]

source_line.py
`-- class SourceLine

split_lines.py
`-- def split_lines(text: str) -> tuple[SourceLine, ...]

split_table_cells.py
|-- def extract_id(text: str) -> str | None
|-- def extract_refs(text: str) -> tuple[str, ...]
|-- def parse_wiki_links(text: str) -> tuple[WikiLink, ...]
|-- def split_table_cells(line: str) -> tuple[TableCell, ...] | None
`-- def strip_comments(text: str) -> str

table_cell.py
`-- class TableCell

table_row.py
`-- class TableRow

types.py
|-- class DailyPlanDocument
|-- class PlanBlockerView
|-- class PlanItemView
`-- class RecordLocation

wiki_link.py
`-- class WikiLink

write_markdown.py
`-- def write_markdown(document: MarkdownDocument) -> str
```

---

## 3. Sub-Packages (1 Tier Down)
*None (leaf module directory).*
