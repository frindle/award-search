#!/usr/bin/env python3
"""Reference impl for: aw-sched-routes-s9-get-scheduled-new-templa

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES
the spec (a refimpl that goes green while a "Must contain" literal is absent
means the verify is benign).

Adds GET /scheduled/new -> scheduled_edit.html with an EMPTY schedule
(normalize_schedule({})) and mode='new', preserving everything already in
src/webui/scheduled_routes.py.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/webui/scheduled_routes.py'
t = p.read_text()

ANCHOR = '@router.get("/partners")\n'
assert ANCHOR in t, "refimpl anchor not found -- did the target change?"

NEW = r'''def normalize_schedule(raw: Optional[Dict]) -> Dict:
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


'''

t = t.replace(ANCHOR, NEW + ANCHOR, 1)
p.write_text(t)
print("refimpl applied")
