#!/usr/bin/env python3
"""Reference impl for: aw-sched-routes-s12-upserts-then-redirectres

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES the
spec (a refimpl that goes green while a "Must contain" literal is absent means
the verify is benign).

Adds the POST /scheduled/save form route to src/webui/scheduled_routes.py:
it upserts into SCHEDULES (new id when sched_id is blank, existing record
otherwise) and answers with RedirectResponse('/scheduled?saved=1', status_code=303).
Everything already in the file is preserved.
"""
import pathlib

wt = pathlib.Path(__file__).resolve().parent
p = wt / 'src/webui/scheduled_routes.py'
t = p.read_text()

OLD = r'''from fastapi import APIRouter, HTTPException, Request'''
NEW = r'''from fastapi import APIRouter, HTTPException, Request
from starlette.responses import RedirectResponse'''

assert OLD in t and "RedirectResponse" not in t, "refimpl anchor not found -- did the target change?"
t = t.replace(OLD, NEW, 1)

ANCHOR = r'''@router.get("/partners")'''
ADD = r'''def _parse_cap_or_none(value):
    try:
        return parse_cap(value)
    except ValueError:
        return None


@router.post("/scheduled/save")
async def scheduled_save(request: Request):
    """Form POST from scheduled_edit.html. Upserts into SCHEDULES, then
    RedirectResponse('/scheduled?saved=1', status_code=303)."""
    form = await request.form()

    def field(name):
        value = form.get(name)
        return value if isinstance(value, str) else None

    sched_id = (field("sched_id") or "").strip()
    name = (field("name") or "").strip()
    origins = parse_csv(field("origins"))
    destinations = parse_csv(field("destinations"))
    date_ranges = parse_date_ranges(
        [v for v in form.getlist("range_start") if isinstance(v, str)],
        [v for v in form.getlist("range_end") if isinstance(v, str)],
    )
    cabins = [v for v in form.getlist("cabins") if isinstance(v, str)]
    programs = [v for v in form.getlist("programs") if isinstance(v, str)]
    transfer_partners = [v for v in form.getlist("transfer_partners") if isinstance(v, str)]

    filters = {
        "airlines": parse_csv(field("airlines")),
        "max_points": _parse_cap_or_none(field("max_points")),
        "max_taxes": _parse_cap_or_none(field("max_taxes")),
    }

    interval_raw = (field("interval_hours") or "").strip()
    try:
        interval_hours = int(interval_raw) if interval_raw else 6
    except ValueError:
        interval_hours = 6

    notify_pushover = field("notify_pushover") is not None
    enabled = field("enabled") is not None

    existing = SCHEDULES.get(sched_id) if sched_id else None
    record = dict(existing or {})
    record.update({
        "id": sched_id or str(uuid.uuid4()),
        "name": name,
        "origins": origins,
        "destinations": destinations,
        "date_ranges": date_ranges,
        "cabins": cabins,
        "programs": programs,
        "transfer_partners": transfer_partners,
        "filters": filters,
        "interval_hours": interval_hours,
        "notify_pushover": notify_pushover,
        "enabled": enabled,
    })
    # PRESERVES created_at/last_checked/last_results/notified_keys from the existing record on an edit.
    for key in ("created_at", "last_checked", "last_results"):
        if key not in record:
            record[key] = None
    record.setdefault("notified_keys", [])

    SCHEDULES[record["id"]] = record
    return RedirectResponse('/scheduled?saved=1', status_code=303)


@router.get("/partners")'''

assert ANCHOR in t, "refimpl anchor not found -- did the target change?"
t = t.replace(ANCHOR, ADD, 1)

if "import uuid" not in t:
    t = t.replace("from typing import Dict, List, Optional",
                  "import uuid\nfrom typing import Dict, List, Optional", 1)

p.write_text(t)
print("refimpl applied")
