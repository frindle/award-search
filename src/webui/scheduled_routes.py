"""Scheduled-routes Web UI routes: transfer partners for award programs."""
from typing import Dict, List, Optional

from pydantic import BaseModel

from fastapi import APIRouter, HTTPException, Request
from starlette.responses import RedirectResponse
import uuid

from ..scheduled_runner import run_schedule
from ..transfer_partners import list_partners


class RunRequest(BaseModel):
    program: str | None = None

router = APIRouter(prefix="/api/scheduled")

TEMPLATES = []

SCHEDULES: Dict[str, Dict] = {}


def init(templates):
    global TEMPLATES
    TEMPLATES = templates


def set_schedules(schedules):
    global SCHEDULES
    SCHEDULES = schedules


@router.get("/templates")
def scheduled_templates():
    return {"templates": TEMPLATES}


@router.get("/page/{name}")
def scheduled_page(request: Request, name: str):
    try:
        return TEMPLATES.TemplateResponse(name, {"request": request})
    except Exception:
        raise HTTPException(status_code=404, detail={"error": "template not found", "name": name})


def normalize_schedule(raw: Optional[Dict]) -> Dict:
    """Coerce raw schedule input into the full shape scheduled_edit.html renders."""
    raw = dict(raw or {})
    filters = dict(raw.get("filters") or {})
    return {
        "id": raw.get("id"),
        "name": raw.get("name", ""),
        "origins": list(raw.get("origins") or []),
        "destinations": list(raw.get("destinations") or []),
        "date_ranges": list(raw.get("date_ranges") or []),
        "cabins": list(raw.get("cabins") or []),
        "programs": list(raw.get("programs") or []),
        "transfer_partners": list(raw.get("transfer_partners") or []),
        "filters": {
            "airlines": list(filters.get("airlines") or []),
            "max_points": filters.get("max_points"),
            "max_taxes": filters.get("max_taxes"),
        },
        "interval_hours": raw.get("interval_hours", 6),
        "notify_pushover": bool(raw.get("notify_pushover", False)),
        "enabled": bool(raw.get("enabled", True)),
    }


@router.get("/scheduled/new")
def scheduled_new(request: Request):
    return TEMPLATES.TemplateResponse(
        "scheduled_edit.html",
        {
            "request": request,
            "schedule": normalize_schedule({}),
            "mode": "new",
            "programs": [],
            "partners": [],
            "error": None,
        },
    )


@router.get("/scheduled/{sched_id}/edit")
def scheduled_edit(request: Request, sched_id: str):
    schedule = SCHEDULES.get(sched_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail={"error": "schedule not found", "sched_id": sched_id})
    return TEMPLATES.TemplateResponse(
        "scheduled_edit.html",
        {
            "request": request,
            "schedule": normalize_schedule(schedule),
            "mode": "edit",
            "programs": [],
            "partners": [],
            "error": None,
        },
    )


@router.get("/{sched_id}/result")
def scheduled_result(request: Request, sched_id: str):
    schedule = SCHEDULES.get(sched_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail={"error": "schedule not found", "sched_id": sched_id})
    results = list(schedule.get("last_results") or [])
    return TEMPLATES.TemplateResponse(
        "scheduled_result.html",
        {"request": request, "schedule": schedule, "results": results},
    )


@router.post("/scheduled/save")
async def scheduled_save(request: Request):
    form = await request.form()

    sched_id = (form.get("sched_id") or "").strip() if isinstance(form.get("sched_id"), str) else ""
    name = (form.get("name") or "") if isinstance(form.get("name"), str) else ""
    origins = parse_csv(form.get("origins"))
    destinations = parse_csv(form.get("destinations"))
    date_ranges = parse_date_ranges(
        form.getlist("range_start"), form.getlist("range_end"))
    cabins = list(form.getlist("cabins"))
    programs = list(form.getlist("programs"))
    transfer_partners = list(form.getlist("transfer_partners"))

    airlines = parse_csv(form.get("airlines"))
    try:
        max_points = parse_cap(form.get("max_points"))
    except ValueError:
        max_points = None
    try:
        max_taxes = parse_cap(form.get("max_taxes"))
    except ValueError:
        max_taxes = None

    interval_raw = form.get("interval_hours")
    try:
        interval_hours = int(str(interval_raw).strip()) if str(interval_raw or "").strip() else 6
    except (ValueError, TypeError):
        interval_hours = 6

    notify_pushover = "notify_pushover" in form
    enabled = "enabled" in form

    schedule = {
        "id": sched_id or str(uuid.uuid4()),
        "name": name,
        "origins": origins,
        "destinations": destinations,
        "date_ranges": date_ranges,
        "cabins": cabins,
        "programs": programs,
        "transfer_partners": transfer_partners,
        "filters": {"airlines": airlines, "max_points": max_points, "max_taxes": max_taxes},
        "interval_hours": interval_hours,
        "notify_pushover": notify_pushover,
        "enabled": enabled,
    }

    if sched_id and sched_id in SCHEDULES:
        existing = dict(SCHEDULES[sched_id])
        for key in ("created_at", "last_checked", "last_results", "notified_keys"):
            schedule[key] = existing.get(key)
        SCHEDULES[sched_id] = schedule
    else:
        for key in ("created_at", "last_checked", "last_results"):
            schedule[key] = None
        schedule["notified_keys"] = []
        SCHEDULES[schedule["id"]] = schedule

    return RedirectResponse('/scheduled?saved=1', status_code=303)


class EditRequest(BaseModel):
    name: Optional[str] = None
    origins: Optional[List[str]] = None
    destinations: Optional[List[str]] = None
    date_ranges: Optional[List[Dict]] = None
    cabins: Optional[List[str]] = None
    programs: Optional[List[str]] = None
    transfer_partners: Optional[List[str]] = None
    filters: Optional[Dict] = None
    interval_hours: Optional[int] = None
    notify_pushover: Optional[bool] = None
    enabled: Optional[bool] = None


@router.post("/{sched_id}")
def scheduled_edit_save(sched_id: str, body: EditRequest):
    schedule = SCHEDULES.get(sched_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail={"error": "schedule not found", "sched_id": sched_id})
    updated = dict(schedule)
    for field in ("name", "origins", "destinations", "date_ranges", "cabins",
                  "programs", "transfer_partners", "filters", "interval_hours",
                  "notify_pushover", "enabled"):
        value = getattr(body, field)
        if value is not None:
            updated[field] = value
    # PRESERVES created_at/last_checked/last_results/notified_keys from the existing record on an edit.
    for key in ("created_at", "last_checked", "last_results", "notified_keys"):
        if key in schedule:
            updated[key] = schedule[key]
        else:
            updated[key] = [] if key == "notified_keys" else None
    SCHEDULES[sched_id] = updated
    return {"schedule": normalize_schedule(updated)}


def delete_schedule(sched_id: str):
    if sched_id not in SCHEDULES:
        raise HTTPException(status_code=404, detail={"error": "schedule not found", "sched_id": sched_id})
    del SCHEDULES[sched_id]


@router.post("/{sched_id}/delete")
def scheduled_delete(sched_id: str):
    delete_schedule(sched_id)
    return RedirectResponse('/scheduled', status_code=303)


@router.post("/{sched_id}/toggle")
def scheduled_toggle(sched_id: str):
    schedule = SCHEDULES.get(sched_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail={"error": "schedule not found", "sched_id": sched_id})
    updated = dict(schedule)
    updated["enabled"] = not bool(schedule.get("enabled", True))
    SCHEDULES[sched_id] = updated
    return RedirectResponse('/scheduled', status_code=303)


@router.get("/partners")
def scheduled_partners():
    return {"partners": list_partners()}


@router.get("/partners/{code}")
def scheduled_partner(code: str):
    for partner in list_partners():
        if partner["code"].lower() == code.lower():
            return dict(partner)
    raise HTTPException(status_code=404, detail={"error": "partner not found", "code": code})


@router.post("/run")
def scheduled_run(body: RunRequest):
    if not body.program:
        raise HTTPException(status_code=422, detail={"error": "program is required", "code": "invalid_program"})
    return run_schedule(program=body.program)


def parse_csv(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def parse_date_ranges(starts: List[str], ends: List[str]) -> List[Dict]:
    """Pair start/end date strings into {"start": ..., "end": ...} dicts.

    Entries are stripped; blank entries are dropped. Each surviving start is
    paired with the end at the same index, or None when no such end exists.
    Extra ends beyond the number of starts are ignored.
    """
    starts = [s.strip() for s in (starts or []) if s and s.strip()]
    ends = [e.strip() for e in (ends or []) if e and e.strip()]
    ranges = []
    for i, start in enumerate(starts):
        end = ends[i] if i < len(ends) else None
        ranges.append({"start": start, "end": end})
    return ranges


def parse_cap(value: Optional[str]) -> Optional[float|int]:
    """Parse a cap value from form input."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        raise ValueError("invalid cap value") from None
    if number.is_integer():
        return int(number)
    return number
