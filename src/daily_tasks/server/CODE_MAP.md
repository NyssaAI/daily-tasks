# Code Map: `server`
[Up: daily_tasks](../CODE_MAP.md)

## 1. Upward Ingress
Immediate caller and integration context:
* **Caller**: [`../cli.py`](../cli.py) -> `cli`

---

## 2. Local Interface & Public Surface
* **Responsibility**: Expose the MCP stdio server that drives the deterministic planning session.
* **Ubiquitous Language Concepts**: [`Planning Session`](../../../docs/GLOSSARY.md), [`Workspace`](../../../docs/GLOSSARY.md)

```text
__init__.py
`-- (no public symbols)

__main__.py
`-- (no public symbols)

harness_message_intake.py
|-- def fetch_window_reply( cursors: Result[FetchCursors], sources: Sequence[str], now: datetime, initial_lookback_days: int ) -> dict[str, JsonValue]
|-- def harness_message_intake( raw_messages: Sequence[Mapping[str, JsonValue]], checked_sources: Sequence[str], snapshot: WorkspaceSnapshot, cursor_store: CursorStore | None, now: datetime, initial_lookback_days: int, ) -> Result[HarnessIntake]
`-- def saved_cursors(cursor_store: CursorStore | None, workspace_root: str) -> Result[FetchCursors]

live_session.py
`-- class LiveSession

markdown_workspace_reader.py
`-- class MarkdownWorkspaceReader
    |-- def __init__( self, settings: ServerSettings, communication: CommunicationPort | None = None, cursor_store: CursorStore | None = None, ) -> None
    `-- def read(self, now: datetime) -> Result[WorkspaceSnapshot]

mcp_server.py
`-- class McpServer
    |-- def __init__( self, tools: PlanningSessionPort, version: str, secrets: SecretTools | None = None ) -> None
    `-- def handle(self, message: str) -> str | None

new_uuid7.py
`-- def new_uuid7(now_ms: Callable[[], int] | None = None, random_bytes: Callable[[int], bytes] | None = None) -> UUID

planning_session_port.py
`-- class PlanningSessionPort(Protocol)
    |-- def start_session( self, date: str | None = None, focus: str | None = None, messages: Sequence[Mapping[str, JsonValue]] = (), checked_sources: Sequence[str] = (), workspace_root: str | None = None, ) -> ToolBody
    |-- def get_fetch_window( self, sources: Sequence[str] = ("gmail", "slack"), workspace_root: str | None = None, ) -> ToolBody
    |-- def get_session_state(self, session_id: str) -> ToolBody
    |-- def execute_operations( self, session_id: str, original_words: str, operations: Sequence[Mapping[str, JsonValue]] = (), verdicts: Sequence[Mapping[str, JsonValue]] = (), ) -> ToolBody
    |-- def advance_screen(self, session_id: str, target_screen: int) -> ToolBody
    |-- def confirm_plan(self, session_id: str, confirmed: bool) -> ToolBody
    `-- def cancel_session(self, session_id: str) -> ToolBody

planning_tools.py
`-- class PlanningTools
    |-- def __init__( self, settings: ServerSettings, reader: WorkspaceReader, store: LocalFileStore, clock: Callable[[], datetime], new_id: Callable[[], UUID], cursor_store: CursorStore | None = None, ) -> None
    |-- def start_session( self, date: str | None = None, focus: str | None = None, messages: Sequence[Mapping[str, JsonValue]] = (), checked_sources: Sequence[str] = (), workspace_root: str | None = None, ) -> ToolBody
    |-- def get_fetch_window( self, sources: Sequence[str] = ("gmail", "slack"), workspace_root: str | None = None ) -> ToolBody
    |-- def get_session_state(self, session_id: str) -> ToolBody
    |-- def execute_operations( self, session_id: str, original_words: str, operations: Sequence[Mapping[str, JsonValue]] = (), verdicts: Sequence[Mapping[str, JsonValue]] = (), ) -> ToolBody
    |-- def advance_screen(self, session_id: str, target_screen: int) -> ToolBody
    |-- def confirm_plan(self, session_id: str, confirmed: bool) -> ToolBody
    `-- def cancel_session(self, session_id: str) -> ToolBody

planning_tools_dispatcher.py
|-- class PlanningToolsDispatcher
|   |-- def __init__( self, overrides: ServerOverrides, clock: Callable[[], datetime], new_id: Callable[[], UUID], ) -> None
|   |-- def start_session( self, date: str | None = None, focus: str | None = None, messages: Sequence[Mapping[str, JsonValue]] = (), checked_sources: Sequence[str] = (), workspace_root: str | None = None, ) -> ToolBody
|   |-- def get_fetch_window( self, sources: Sequence[str] = ("gmail", "slack"), workspace_root: str | None = None, ) -> ToolBody
|   |-- def get_session_state(self, session_id: str) -> ToolBody
|   |-- def execute_operations( self, session_id: str, original_words: str, operations: Sequence[Mapping[str, JsonValue]] = (), verdicts: Sequence[Mapping[str, JsonValue]] = (), ) -> ToolBody
|   |-- def advance_screen(self, session_id: str, target_screen: int) -> ToolBody
|   |-- def confirm_plan(self, session_id: str, confirmed: bool) -> ToolBody
|   `-- def cancel_session(self, session_id: str) -> ToolBody
`-- def tool_dispatch_error( tool: str, message: str, category: ErrorCategory | str = ErrorCategory.VALIDATION, ) -> ToolBody

resolve_server_settings.py
|-- def read_layered_profile( workspace_root: Path | None, config_dir: Path | None = None, ) -> Result[dict[str, JsonValue]]
`-- def resolve_server_settings( workspace_root: Path | None, overrides: ServerOverrides = _DEFAULT_OVERRIDES, ) -> Result[ServerSettings]

secret_tools.py
`-- class SecretTools
    |-- def __init__( self, open_service: Callable[[], Result[SecretCaptureService]], timeout_seconds: float = 300.0, ) -> None
    `-- def capture_secret( self, namespace: str, key: str, prompt_message: str | None = None, provider: str | None = None ) -> dict[str, JsonValue]

serve_stdio.py
`-- def serve_stdio(server: McpServer, reader: TextIO, writer: TextIO) -> int

start_session_reply.py
`-- def start_session_reply( snapshot: WorkspaceSnapshot, harness_sources: Sequence[str], pending: int ) -> tuple[str, dict[str, JsonValue]]

tool_definitions.py
|-- SECRET_TOOL_DEFINITIONS: Final[tuple[dict[str, JsonValue], ...]]
`-- TOOL_DEFINITIONS: Final[tuple[dict[str, JsonValue], ...]]

tool_reply.py
`-- def tool_reply( tool: str, outcome: Result[str], session: SessionState | None, screen: str | None = None, expected_tool: str | None = None, payload: Mapping[str, JsonValue] | None = None, ) -> dict[str, JsonValue]

types.py
|-- class HarnessIntake
|-- class ServerOverrides
|-- class ServerSettings
`-- class WorkspaceSnapshot

workspace_reader.py
`-- class WorkspaceReader(Protocol)
    `-- def read(self, now: datetime) -> Result[WorkspaceSnapshot]
```

---

## 3. Sub-Packages (1 Tier Down)
*None (leaf module directory).*
