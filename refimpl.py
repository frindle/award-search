#!/usr/bin/env python3
"""Reference impl for: aw-sched-routes-s14-post-scheduled-sched-id

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES
the spec (a refimpl that goes green while a "Must contain" literal is absent
means the verify is benign).

Adds exactly one route -- POST /{sched_id}/toggle -- to the existing router in
src/webui/scheduled_routes.py, immediately after scheduled_delete. Everything
else in the file is preserved byte-for-byte.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/webui/scheduled_routes.py'
t = p.read_text()

OLD = r'''@router.post("/{sched_id}/delete")
def scheduled_delete(sched_id: str):
    delete_schedule(sched_id)
    return RedirectResponse('/scheduled', status_code=303)
'''

NEW = r'''@router.post("/{sched_id}/delete")
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
'''

assert OLD in t, "refimpl anchor not found -- did the target change?"
if '"/{sched_id}/toggle"' in t:
    print("refimpl already applied; nothing to do")
else:
    p.write_text(t.replace(OLD, NEW, 1))
    print("refimpl applied")
