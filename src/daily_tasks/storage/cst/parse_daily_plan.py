# Responsibility: Map a parsed daily plan Markdown record onto a daily plan document.
# Public interface:
# `-- parse_daily_plan(document, location, base)
"""Daily plan parser: the inverse of `render_daily_plan` for every value the Markdown shows."""

import hashlib
import re
from collections.abc import Mapping
from typing import Final

from nyssa_ai_result import Ok, Result, fail_error, ok
from pydantic import TypeAdapter

from daily_tasks.domain import DailyPlan, DailyPlanEntry
from daily_tasks.storage.cst.daily_plan_renderer import SECTION_TITLES
from daily_tasks.storage.cst.nodes import MarkdownDocument
from daily_tasks.storage.cst.parse_error import ParseError
from daily_tasks.storage.cst.read_blocker_row import read_blocker_row
from daily_tasks.storage.cst.read_item_row import read_item_row
from daily_tasks.storage.cst.record_fields import RecordFields
from daily_tasks.storage.cst.types import DailyPlanDocument, PlanBlockerView, PlanItemView, RecordLocation
from daily_tasks.storage.cst.writer import write_markdown

_PLAN: Final[TypeAdapter[DailyPlan]] = TypeAdapter(DailyPlan)
_SUMMARY: Final = re.compile(r"Open projects:\s*(\d+)\s+Open tasks:\s*(\d+)\s+Late tasks:\s*(\d+)")
_FOCUS: Final = re.compile(r"^\*\*Focus:\*\*\s*(.*?)\s*$", re.MULTILINE)
_DECISION: Final = re.compile(r"^- \*\*\[([^\]]+)\]\*\*\s+(.*?)\?\s+(.*)$")
_SECTION_KEYS: Final[Mapping[str, str]] = {title.casefold(): key for key, title in SECTION_TITLES.items()}

type _Values = dict[str, object]


def _items(document: MarkdownDocument) -> Result[list[tuple[str, PlanItemView, bool]], ParseError]:
    rows: list[tuple[str, PlanItemView, bool]] = []
    for section in document.sections:
        key = _SECTION_KEYS.get(section.heading.title.casefold())
        if section.heading.level != 3 or key is None:
            continue
        for row in section.table_rows:
            read = read_item_row(row)
            if isinstance(read, ParseError):
                return fail_error(read)
            rows.append((key, read[0], read[1]))
    return ok(rows)


def _blockers(fields: RecordFields) -> Result[list[tuple[PlanBlockerView, tuple[int, ...]]], ParseError]:
    section = fields.section("Blockers Under Active Resolution")
    rows: list[tuple[PlanBlockerView, tuple[int, ...]]] = []
    for row in section.table_rows if section else ():
        read = read_blocker_row(row)
        if isinstance(read, ParseError):
            return fail_error(read)
        rows.append(read)
    return ok(rows)


def _entries(
    items: list[tuple[str, PlanItemView, bool]], blocker_ids: set[str], base: DailyPlan | None, added_at: object
) -> list[_Values]:
    known: Mapping[str, DailyPlanEntry] = {str(e.item_id): e for e in base.entries} if base else {}
    entries: list[_Values] = []
    for section, view, is_carried in items:
        entry = known.get(view.item_id)
        entries.append(
            {
                "item_type": entry.item_type if entry else "task",
                "item_id": view.item_id,
                "section": section,
                "carried_from": entry.carried_from if entry and is_carried else None,
                "added_at": entry.added_at if entry else added_at,
            }
        )
    if base is None:
        return entries
    listed = {view.item_id for _, view, _ in items}
    scheduled = [e for e in base.entries if e.item_type == "blocker" and str(e.item_id) in blocker_ids - listed]
    order = {str(e.item_id): index for index, e in enumerate(base.entries)}
    entries += [
        {
            "item_type": e.item_type,
            "item_id": e.item_id,
            "section": e.section,
            "carried_from": e.carried_from,
            "added_at": e.added_at,
        }
        for e in scheduled
    ]
    return sorted(entries, key=lambda e: order.get(str(e["item_id"]), len(order)))


def _section_lines(fields: RecordFields, title: str) -> list[str]:
    section = fields.section(title)
    lines = fields.document.lines[section.heading.line_index + 1 : section.end_index] if section else ()
    return [line.text for line in lines]


def _plan_values(fields: RecordFields, location: RecordLocation, base: DailyPlan | None) -> _Values:
    values = fields.frontmatter_values()
    text = write_markdown(fields.document)
    summary = _SUMMARY.search(text)
    focus = _FOCUS.search(text)
    decisions = [m.groups() for m in map(_DECISION.match, _section_lines(fields, "Decisions")) if m]
    return {
        "id": values.get("id"),
        "type": values.get("type"),
        "local_date": values.get("date"),
        "timezone": values.get("timezone"),
        "path": location.path,
        "created_at": values.get("created_at"),
        "updated_at": values.get("updated_at"),
        "content_hash": "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "focus": focus.group(1) if focus else None,
        "summary": dict(zip(("open_projects", "open_tasks", "late_tasks"), map(int, summary.groups()), strict=True))
        if summary
        else None,
        "removed_item_ids": base.removed_item_ids if base else (),
        "decisions": tuple({"id": i, "question": f"{q}?", "resolution": r} for i, q, r in decisions),
        "notes": tuple(line[2:] for line in _section_lines(fields, "Notes and references") if line.startswith("- ")),
        "source": location.source,
    }


def parse_daily_plan(
    document: MarkdownDocument, location: RecordLocation, base: DailyPlan | None = None
) -> Result[DailyPlanDocument, ParseError]:
    """Build a daily plan document from its Markdown.

    The Markdown is authoritative for every value it shows. Values it cannot show come from `base`
    (the stored plan, when known): entry `added_at`, `item_type` and `carried_from` dates, blocker
    entries scheduled for the day (shown only in the blocker table) and `removed_item_ids`. Without
    `base`, rows are tasks added at `updated_at` with no carry date. `content_hash` is the SHA-256 of
    the record text. Fails with `invalid-plan-row` or `invalid-record`.
    """
    fields = RecordFields(document)
    items = _items(document)
    if not isinstance(items, Ok):
        return items
    blockers = _blockers(fields)
    if not isinstance(blockers, Ok):
        return blockers
    values = fields.frontmatter_values()
    numbers = {index + 1: view.item_id for index, (_, view, _) in enumerate(items.value)}
    plan_values = _plan_values(fields, location, base)
    plan_values["entries"] = tuple(
        _entries(items.value, {view.blocker_id for view, _ in blockers.value}, base, values.get("updated_at"))
    )
    plan_values["blockers"] = tuple(
        {"blocker_id": view.blocker_id, "blocks": tuple(numbers[n] for n in rows if n in numbers)}
        for view, rows in blockers.value
    )
    plan = RecordFields.validate(_PLAN, plan_values)
    if not isinstance(plan, Ok):
        return plan
    owner, tags, maturity, version = (values.get(k) for k in ("owner", "tags", "document-maturity", "record_version"))
    return ok(
        DailyPlanDocument(
            plan=plan.value,
            owner=owner if isinstance(owner, str) else location.inherited_owner or "",
            tags=tags if isinstance(tags, tuple) else (),
            maturity=maturity if isinstance(maturity, str) else "draft",
            record_version=version if isinstance(version, int) and not isinstance(version, bool) else 1,
            items=tuple(view for _, view, _ in items.value),
            blockers=tuple(view for view, _ in blockers.value),
        )
    )
