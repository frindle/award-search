#!/usr/bin/env python3
"""Reference impl for: aw-sched-routes-s13-post-scheduled-sched-id

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES the
spec (a refimpl that goes green while a "Must contain" literal is absent means
the verify is benign).

Adds POST /api/scheduled/{sched_id}/delete -> delete_schedule(sched_id) then
RedirectResponse('/scheduled', status_code=303), preserving everything already
in src/webui/scheduled_routes.py.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/webui/scheduled_routes.py'
t = p.read_text()

OLD = r'''@router.get("/partners")'''

NEW = r'''def delete_schedule(sched_id: str):
    """Remove a schedule by id; raise 404 when the id is unknown."""
    if sched_id not in SCHEDULES:
        raise HTTPException(status_code=404, detail={"error": "schedule not found", "sched_id": sched_id})
    del SCHEDULES[sched_id]


@router.post("/{sched_id}/delete")
def scheduled_delete(sched_id: str):
    delete_schedule(sched_id)
    return RedirectResponse('/scheduled', status_code=303)


@router.get("/partners")'''

assert OLD in t, "refimpl anchor not found -- did the target change?"
p.write_text(t.replace(OLD, NEW, 1))
print("refimpl applied")
