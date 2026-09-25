"""Scheduled-routes Web UI routes: transfer partners for award programs."""
from typing import Dict, List, Optional

from pydantic import BaseModel

from fastapi import APIRouter, HTTPException, Request

from ..scheduled_runner import run_schedule
from ..transfer_partners import list_partners


class RunRequest(BaseModel):
    program: str | None = None

router = APIRouter(prefix="/api/scheduled")

TEMPLATES = []


def init(templates):
    global TEMPLATES
    TEMPLATES = templates


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
