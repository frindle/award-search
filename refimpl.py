#!/usr/bin/env python3
"""Reference impl for: scheduled_routes

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES
the spec (a refimpl that goes green while a "Must contain" literal is absent
means the verify is benign).

The target currently holds only a placeholder stub, so this writer emits the
complete module from scratch.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/webui/scheduled_routes.py'
p.parent.mkdir(parents=True, exist_ok=True)

SOLUTION = '''"""Scheduled award-search routes.

Backs the existing scheduled.html / scheduled_edit.html / scheduled_result.html
templates with an APIRouter plus init(templates), which stores the shared
Jinja2Templates instance from app.py before the router is included.
"""
import json
import re
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates: Optional[Jinja2Templates] = None


def init(templates: Jinja2Templates) -> None:
    """Store the app's Jinja2Templates instance for use by these routes."""
    globals()["templates"] = templates


BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORE_PATH = BASE_DIR / "credentials" / "scheduled.json"

AIRPORT_RE = re.compile(r"^[A-Z]{3}$")
CABINS = ("economy", "premium_economy", "business", "first")


def _load_schedules() -> List[Dict[str, Any]]:
    try:
        data = json.loads(STORE_PATH.read_text())
    except (OSError, ValueError):
        return []
    if isinstance(data, dict) and isinstance(data.get("schedules"), list):
        return data["schedules"]
    return data if isinstance(data, list) else []


def _save_schedules(schedules: List[Dict[str, Any]]) -> None:
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STORE_PATH.write_text(json.dumps({"schedules": schedules}, indent=2))


def _parse_airports(raw: str) -> Optional[List[str]]:
    codes = [c.strip().upper() for c in raw.split(",") if c.strip()]
    if not codes or any(not AIRPORT_RE.match(c) for c in codes):
        return None
    return codes


def _parse_date_ranges(raw: str) -> List[Dict[str, str]]:
    ranges = []
    range_re = re.compile(
        r"^(\d{4}-\d{2}-\d{2})(?:-(\d{4}-\d{2}-\d{2}))?$")
    for part in (s.strip() for s in raw.split(";") if s.strip()):
        m = range_re.match(part)
        if not m:
            return None
        start_s, end_s = m.group(1), m.group(2)
        try:
            date.fromisoformat(start_s)
            if end_s:
                date.fromisoformat(end_s)
        except ValueError:
            return None
        ranges.append({"start": start_s, "end": end_s})
    return ranges


def _parse_int(raw: str, default: int, lo: int = 1, hi: int = 24 * 30) -> Optional[int]:
    try:
        value = int(str(raw).strip())
    except (TypeError, ValueError):
        return None
    if not (lo <= value <= hi):
        return None
    return value


def _parse_float(raw: str) -> Optional[float]:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    return value if value >= 0 else None


def _render(request: Request, name: str, context: Dict[str, Any]) -> HTMLResponse:
    return templates.TemplateResponse(name, {"request": request, **context})


@router.get("/scheduled", response_class=HTMLResponse)
async def scheduled_list(request: Request):
    schedules = _load_schedules()
    groups = []
    try:
        from ..seats_aero import SeatsAeroClient
        client = SeatsAeroClient()
        groups = getattr(client, "groups", None) or []
    except Exception:
        groups = []
    return _render(request, "scheduled.html", {
        "schedules": {s["id"]: s for s in schedules},
        "sid": None,
        "schedule": None,
        "mode": "list",
        "programs": [],
        "transfer_partners": [],
        "groups": groups,
        "seats_aero_configured": True,
    })


@router.get("/scheduled/new", response_class=HTMLResponse)
async def scheduled_new(request: Request):
    return _render(request, "scheduled_edit.html", {
        "mode": "new",
        "schedule": {"filters": {}},
        "error": None,
        "programs": [],
        "transfer_partners": [],
        "cabins": CABINS,
    })


@router.get("/scheduled/{sid}/edit", response_class=HTMLResponse)
async def scheduled_edit(sid: str, request: Request):
    schedules = _load_schedules()
    schedule = next((s for s in schedules if s.get("id") == sid), None)
    if schedule is None:
        return RedirectResponse(url="/scheduled?error=not_found", status_code=303)
    return _render(request, "scheduled_edit.html", {
        "mode": "edit",
        "schedule": schedule,
        "error": None,
        "programs": [],
        "transfer_partners": [],
        "cabins": CABINS,
    })


@router.post("/scheduled/save", response_class=HTMLResponse)
async def scheduled_save(
    request: Request,
    id: str = Form(""),
    name: str = Form(""),
    origins: str = Form(...),
    destinations: str = Form(...),
    date_ranges: str = Form(""),
    cabins: List[str] = Form(default=[]),
    programs: List[str] = Form(default=[]),
    transfer_partners: List[str] = Form(default=[]),
    interval_hours: str = Form("6"),
    notify_pushover: bool = Form(False),
    filter_airlines: str = Form(""),
    max_points: str = Form(""),
    max_taxes: str = Form(""),
):
    origin_list = _parse_airports(origins)
    dest_list = _parse_airports(destinations)
    if origin_list is None or dest_list is None:
        return _render(request, "scheduled_edit.html", {
            "mode": "new" if not id else "edit",
            "schedule": {"filters": {}},
            "error": "Invalid airport code. Use 3-letter codes (e.g., JFK, LAX).",
            "programs": [],
            "transfer_partners": [],
            "cabins": CABINS,
        })

    ranges = _parse_date_ranges(date_ranges) if date_ranges.strip() else []
    if ranges is None:
        return _render(request, "scheduled_edit.html", {
            "mode": "new" if not id else "edit",
            "schedule": {"filters": {}},
            "error": "Invalid date range. Use YYYY-MM-DD or START-END.",
            "programs": [],
            "transfer_partners": [],
            "cabins": CABINS,
        })

    interval = _parse_int(interval_hours, 6)
    if interval is None:
        return _render(request, "scheduled_edit.html", {
            "mode": "new" if not id else "edit",
            "schedule": {"filters": {}},
            "error": "Interval must be a whole number of hours between 1 and 720.",
            "programs": [],
            "transfer_partners": [],
            "cabins": CABINS,
        })

    cabin_list = [c for c in cabins if c in CABINS]
    filters = {
        "airlines": [a.strip().upper() for a in filter_airlines.split(",") if a.strip()],
        "max_points": _parse_float(max_points),
        "max_taxes": _parse_float(max_taxes),
    }

    schedules = _load_schedules()
    now = datetime.now().isoformat()
    if id:
        schedule = next((s for s in schedules if s.get("id") == id), None)
        if schedule is None:
            return RedirectResponse(url="/scheduled?error=not_found", status_code=303)
        schedule.update({
            "name": name.strip(),
            "origins": origin_list,
            "destinations": dest_list,
            "date_ranges": ranges,
            "cabins": cabin_list,
            "programs": programs,
            "transfer_partners": transfer_partners,
            "interval_hours": interval,
            "notify_pushover": notify_pushover,
            "filters": filters,
        })
    else:
        schedules.append({
            "id": f"sched_{uuid.uuid4().hex[:12]}",
            "name": name.strip(),
            "origins": origin_list,
            "destinations": dest_list,
            "date_ranges": ranges,
            "cabins": cabin_list,
            "programs": programs,
            "transfer_partners": transfer_partners,
            "interval_hours": interval,
            "notify_pushover": notify_pushover,
            "filters": filters,
            "enabled": True,
            "created_at": now,
            "last_checked": None,
            "last_hit_count": None,
        })
    _save_schedules(schedules)
    return RedirectResponse(url="/scheduled?saved=1", status_code=303)


@router.post("/scheduled/{sid}/toggle")
async def scheduled_toggle(sid: str):
    schedules = _load_schedules()
    schedule = next((s for s in schedules if s.get("id") == sid), None)
    if schedule is None:
        return RedirectResponse(url="/scheduled?error=not_found", status_code=303)
    schedule["enabled"] = not bool(schedule.get("enabled"))
    _save_schedules(schedules)
    state = "paused" if schedule["enabled"] is False else "enabled"
    return RedirectResponse(url=f"/scheduled?{state}=1", status_code=303)


@router.post("/scheduled/{sid}/delete")
async def scheduled_delete(sid: str):
    schedules = _load_schedules()
    remaining = [s for s in schedules if s.get("id") != sid]
    if len(remaining) == len(schedules):
        return RedirectResponse(url="/scheduled?error=not_found", status_code=303)
    _save_schedules(remaining)
    return RedirectResponse(url="/scheduled?deleted=1", status_code=303)


@router.post("/scheduled/{sid}/run", response_class=HTMLResponse)
async def scheduled_run(sid: str, request: Request):
    schedules = _load_schedules()
    schedule = next((s for s in schedules if s.get("id") == sid), None)
    if schedule is None:
        return RedirectResponse(url="/scheduled?error=not_found", status_code=303)

    results: List[Dict[str, Any]] = []
    errors: List[str] = []
    try:
        from ..seats_aero import SeatsAeroClient
        client = SeatsAeroClient()
    except Exception as e:
        errors.append(f"Seats.aero unavailable: {e}")
        client = None

    if client is not None:
        for origin in schedule.get("origins", []):
            for destination in schedule.get("destinations", []):
                for start in [r["start"] for r in schedule.get("date_ranges", [])] or [""]:
                    try:
                        dep = date.fromisoformat(start) if start else None
                        found = client.search(
                            origin=origin, destination=destination,
                            start_date=dep, end_date=dep,
                            cabins=schedule.get("cabins") or None,
                            programs=schedule.get("programs") or None,
                        )
                    except Exception as e:
                        errors.append(f"{origin} {destination}: {e}")
                        continue
                    for avail in found:
                        results.append({
                            "source": getattr(avail, "source", ""),
                            "date": start,
                            "cost": 0,
                            "seats": 0,
                            "airlines": [],
                            "cabin": (schedule.get("cabins") or [""])[0],
                            "origin": origin,
                            "destination": destination,
                            "taxes": 0.0,
                            "booking_url": "",
                        })

    schedule["last_checked"] = datetime.now().isoformat()
    schedule["last_hit_count"] = len(results)
    _save_schedules(schedules)

    return _render(request, "scheduled_result.html", {
        "schedule": schedule,
        "results": results,
        "errors": errors,
    })
'''

p.write_text(SOLUTION)
print("refimpl applied")
