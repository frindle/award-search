#!/usr/bin/env python3
"""Reference impl for: aw-sched-routes-s19-get-api-scheduled-sched

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES
the spec (a refimpl that goes green while a "Must contain" literal is absent
means the verify is benign).

Adds GET /api/scheduled/{sched_id}/preview plus effective_programs() to
src/webui/scheduled_routes.py, preserving everything already in the file.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/webui/scheduled_routes.py'
t = p.read_text()

OLD = r'''@router.post("/run")
def scheduled_run(body: RunRequest):'''

NEW = r'''def effective_programs(schedule: Dict) -> List[str]:
    """Programs in effect for a schedule: its own programs if set, else every configured program id."""
    own = [p.strip() for p in (schedule.get("programs") or []) if isinstance(p, str) and p.strip()]
    if own:
        return sorted(set(own))
    from ..search.programs.base import load_programs_config
    return sorted(load_programs_config().keys())


@router.get("/{sched_id}/preview")
def scheduled_preview(sched_id: str):
    schedule = SCHEDULES.get(sched_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail={"error": "schedule not found", "sched_id": sched_id})
    legs = []
    date_ranges = list(schedule.get("date_ranges") or []) or [{}]
    for origin in (schedule.get("origins") or []):
        for destination in (schedule.get("destinations") or []):
            for date_range in date_ranges:
                legs.append({
                    "origin": origin,
                    "destination": destination,
                    "start_date": date_range.get("start"),
                    "end_date": date_range.get("end"),
                })
    return {"legs": legs, "leg_count": len(legs), "programs": effective_programs(schedule)}


@router.post("/run")
def scheduled_run(body: RunRequest):'''

assert OLD in t, "refimpl anchor not found -- did the target change?"
p.write_text(t.replace(OLD, NEW, 1))
print("refimpl applied")
