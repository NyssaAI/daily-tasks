# Code Map: `domain`
[Up: daily_tasks](../CODE_MAP.md)

## 1. Upward Ingress
Immediate caller and integration context:
* **Caller**: [`../adapters/markdown_daily_plan_adapter.py`](../adapters/markdown_daily_plan_adapter.py) -> `markdown_daily_plan_adapter`
* **Caller**: [`../adapters/markdown_project_plan_adapter.py`](../adapters/markdown_project_plan_adapter.py) -> `markdown_project_plan_adapter`
* **Caller**: [`../adapters/communication/communication_multiplexer.py`](../adapters/communication/communication_multiplexer.py) -> `communication_multiplexer`

---

## 2. Local Interface & Public Surface
* **Responsibility**: Expose the domain DTO boundary API.
* **Ubiquitous Language Concepts**: [`Milestone`](../../../docs/GLOSSARY.md), [`Project`](../../../docs/GLOSSARY.md), [`Suggestion`](../../../docs/GLOSSARY.md), [`Task`](../../../docs/GLOSSARY.md)

```text
__init__.py
`-- (no public symbols)

actor.py
`-- class Actor

assign_days.py
`-- class AssignDays

assign_to_day.py
`-- class AssignToDay

attachment.py
`-- class Attachment

background_fetch.py
`-- class BackgroundFetch

background_source.py
`-- class BackgroundSource

blocker.py
`-- class Blocker

blocker_facts.py
`-- class BlockerFacts

blocker_node.py
`-- class BlockerNode

blocker_ref.py
`-- class BlockerRef

blocker_state.py
`-- (no public symbols)

communication_binding.py
`-- class CommunicationBinding

daily_plan.py
`-- class DailyPlan

daily_plan_entry.py
`-- class DailyPlanEntry

daily_plan_summary.py
`-- class DailyPlanSummary

decision_log.py
`-- class DecisionLog

decision_log_entry.py
`-- class DecisionLogEntry

decision_origin.py
`-- (no public symbols)

decision_ref.py
`-- class DecisionRef

diagnostic.py
`-- class Diagnostic

dod_item.py
`-- class DodItem

dod_progress.py
`-- class DodProgress

dropped_task.py
`-- class DroppedTask

dto_config.py
`-- DTO_CONFIG: Final[ConfigDict]

fetch_cursor.py
`-- class FetchCursor

fetch_cursors.py
`-- class FetchCursors

file_store_binding.py
`-- class FileStoreBinding

for_review_message.py
`-- class ForReviewMessage

graph_user.py
`-- class GraphUser

instruction_origin.py
`-- class InstructionOrigin

item_type.py
`-- (no public symbols)

message.py
`-- class Message

message_address.py
`-- class MessageAddress

message_facts.py
`-- class MessageFacts

message_graph.py
`-- class MessageGraph

message_graph_context.py
`-- class MessageGraphContext

message_graph_derived.py
`-- class MessageGraphDerived

message_graph_index.py
`-- class MessageGraphIndex

message_graph_record.py
`-- class MessageGraphRecord

message_graph_summary.py
`-- class MessageGraphSummary

message_link.py
`-- class MessageLink

message_log.py
`-- class MessageLog

message_log_entry.py
`-- class MessageLogEntry

message_source_status.py
`-- class MessageSourceStatus

message_source_tree.py
`-- class MessageSourceTree

message_thread.py
`-- class MessageThread

milestone.py
`-- class Milestone

milestone_facts.py
`-- class MilestoneFacts

milestone_node.py
`-- class MilestoneNode

milestone_tree.py
`-- class MilestoneTree

operation.py
`-- (no public symbols)

operations.py
`-- class Operations

person_index.py
`-- class PersonIndex

plan_item.py
`-- class PlanItem

plan_node.py
`-- class PlanNode

planning_session.py
`-- class PlanningSession

port_config.py
`-- class PortConfig

ports.py
`-- class Ports

project.py
`-- class Project

project_node.py
`-- class ProjectNode

project_tree.py
`-- class ProjectTree

reassign.py
`-- class Reassign

record_change.py
`-- class RecordChange

record_change_origin.py
`-- class RecordChangeOrigin

record_origin.py
`-- class RecordOrigin

record_source_status.py
`-- class RecordSourceStatus

rollover.py
`-- class Rollover

row_ref.py
`-- class RowRef

screen.py
`-- class Screen

secret_string.py
`-- class SecretString
    |-- def __init__(self, value: str) -> None
    `-- def reveal(self) -> str

set_status.py
`-- class SetStatus

source_binding.py
`-- class SourceBinding

spec_ref.py
`-- class SpecRef

state_graph.py
`-- class StateGraph

state_graph_context.py
`-- class StateGraphContext

state_graph_derived.py
`-- class StateGraphDerived

state_graph_index.py
`-- class StateGraphIndex

state_graph_records.py
`-- class StateGraphRecords

state_graph_summary.py
`-- class StateGraphSummary

suggestion.py
`-- class Suggestion

suggestion_origin.py
`-- class SuggestionOrigin

suggestion_target.py
`-- class SuggestionTarget

suggestion_validation.py
`-- class SuggestionValidation

suggestions.py
`-- class Suggestions

task.py
`-- class Task

task_facts.py
`-- class TaskFacts

task_node.py
`-- class TaskNode

thread_facts.py
`-- class ThreadFacts

today.py
`-- class Today

today_selection.py
`-- class TodaySelection

tool_progress.py
`-- class ToolProgress

tool_result.py
`-- (no public symbols)

tool_result_error.py
`-- class ToolResultError

tool_result_ok.py
`-- class ToolResultOk

tool_result_processing.py
`-- class ToolResultProcessing

tool_result_refused.py
`-- class ToolResultRefused

tool_results.py
`-- (no public symbols)

unplan.py
`-- class Unplan

utc_timestamp.py
`-- (no public symbols)

work_state.py
`-- (no public symbols)
```

---

## 3. Sub-Packages (1 Tier Down)
*None (leaf module directory).*
