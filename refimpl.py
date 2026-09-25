#!/usr/bin/env python3
"""Reference impl for: aw-sched-routes-s10-get-scheduled-sched-id-e

Adds GET /api/scheduled/{sched_id}/edit to src/webui/scheduled_routes.py:
renders the same scheduled_edit.html template as /scheduled/new, but with the
loaded schedule and mode='edit'. Unknown sched_id -> 404 (not 500).

Everything already in the file is preserved; this only inserts a SCHEDULES
store + setter next to TEMPLATES/init, and the new route after scheduled_new.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/webui/scheduled_routes.py'
t = p.read_text()

OLD_STORE = r'''TEMPLATES = []


def init(templates):
    global TEMPLATES
    TEMPLATES = templates
'''
NEW_STORE = r'''TEMPLATES = []
SCHEDULES: Dict[str, Dict] = {}


def init(templates):
    global TEMPLATES
    TEMPLATES = templates


def set_schedules(schedules: Optional[Dict[str, Dict]]):
    """Replace the in-memory schedule store keyed by sched_id."""
    global SCHEDULES
    SCHEDULES = dict(schedules or {})
'''

OLD_ANCHOR = r'''@router.get("/partners")
def scheduled_partners():'''
NEW_ANCHOR = r'''@router.get("/scheduled/{sched_id}/edit")
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


@router.get("/partners")
def scheduled_partners():'''

assert OLD_STORE in t, "refimpl anchor (store) not found -- did the target change?"
t = t.replace(OLD_STORE, NEW_STORE, 1)
assert OLD_ANCHOR in t, "refimpl anchor (route insertion point) not found -- did the target change?"
t = t.replace(OLD_ANCHOR, NEW_ANCHOR, 1)

import ast
ast.parse(t)  # refuse to write unparseable source

p.write_text(t)
print("refimpl applied")
