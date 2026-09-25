#!/usr/bin/env python3
"""Reference impl for: aw-sched-routes-s16-render-scheduled-result

Adds the GET /api/scheduled/{sched_id}/result route that renders
'scheduled_result.html' with {request, schedule, results}. Everything already
in src/webui/scheduled_routes.py is preserved; this only inserts one new
route handler between scheduled_edit and parse_csv.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/webui/scheduled_routes.py'
t = p.read_text()

OLD = r'''def parse_csv(value: Optional[str]) -> List[str]:'''

NEW = r'''@router.get("/{sched_id}/result")
def scheduled_result(request: Request, sched_id: str):
    schedule = SCHEDULES.get(sched_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail={"error": "schedule not found", "sched_id": sched_id})
    results = list(schedule.get("last_results") or [])
    return TEMPLATES.TemplateResponse(
        "scheduled_result.html",
        {"request": request, "schedule": schedule, "results": results},
    )


def parse_csv(value: Optional[str]) -> List[str]:'''

assert OLD in t, "refimpl anchor not found -- did the target change?"
p.write_text(t.replace(OLD, NEW, 1))
print("refimpl applied")
