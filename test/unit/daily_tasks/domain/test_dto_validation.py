# Responsibility: Prove the DTOs reject non-UTC timestamps, non-UUIDv7 ids and unknown fields.
# Public interface:
# (none)
"""Boundary validation rules shared by every domain DTO."""

import pytest
from pydantic import JsonValue, TypeAdapter, ValidationError

from conftest import load_spec
from daily_tasks.domain import Operations, Project, ToolResults
from daily_tasks.domain.operations.types import SetStatus
from daily_tasks.domain.tool_results.types import ToolResultRefused

_PROJECT: TypeAdapter[Project] = TypeAdapter(Project)


def _project_with(**changes: JsonValue) -> dict[str, JsonValue]:
    spec = load_spec("project.json")
    assert isinstance(spec, dict)
    return {**spec, **changes}


@pytest.mark.parametrize("timestamp", ["2026-10-20T14:02:11+01:00", "2026-10-20T14:02:11"])
def test_project_non_utc_timestamp_is_rejected(timestamp: str) -> None:
    with pytest.raises(ValidationError):
        _PROJECT.validate_python(_project_with(created_at=timestamp))


def test_project_utc_offset_timestamp_is_accepted() -> None:
    project = _PROJECT.validate_python(_project_with(created_at="2026-10-20T14:02:11+00:00"))

    assert project.created_at.isoformat() == "2026-10-20T14:02:11+00:00"


@pytest.mark.parametrize("record_id", ["0f8fad5b-d9cb-469f-a165-70867728950e", "not-a-uuid"])
def test_project_non_uuid7_id_is_rejected(record_id: str) -> None:
    with pytest.raises(ValidationError):
        _PROJECT.validate_python(_project_with(id=record_id))


def test_project_unknown_field_is_rejected() -> None:
    with pytest.raises(ValidationError):
        _PROJECT.validate_python(_project_with(priority="high"))


def test_operations_kind_selects_operation_type() -> None:
    operations = TypeAdapter(Operations).validate_python(load_spec("operations.json"))

    milestone_status = operations.operations[5]
    assert isinstance(milestone_status, SetStatus)
    assert milestone_status.label == "M2"


def test_tool_results_status_selects_result_type() -> None:
    results = TypeAdapter(ToolResults).validate_python(load_spec("tool-results.json"))

    refused = results[2]
    assert isinstance(refused, ToolResultRefused)
    assert refused.expected_tool == "plan_screen"
