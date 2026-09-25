#!/usr/bin/env python3
"""Reference impl for: aw-sched-routes-s15-post-scheduled-sched-id

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES the
spec (a refimpl that goes green while a "Must contain" literal is absent means
the verify is benign).

Write the SIMPLEST change that makes the verify pass. It doubles as your review
reference when the model's diff comes back.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/webui/scheduled_routes.py'
t = p.read_text()

OLD = r'''from fastapi import APIRouter, HTTPException, Request'''
NEW = r'''import anyio

from fastapi import APIRouter, HTTPException, Request'''

assert OLD in t and "import anyio" not in t, "refimpl anchor not found -- did the target change?"
t = t.replace(OLD, NEW, 1)

OLD2 = r'''@router.post("/run")
def scheduled_run(body: RunRequest):'''
NEW2 = r'''@router.post("/{sched_id}/run")
async def scheduled_run_by_id(sched_id: str):
    schedule = SCHEDULES.get(sched_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail={"error": "schedule not found", "sched_id": sched_id})
    return await anyio.to_thread.run_sync(run_schedule, schedule)


@router.post("/run")
def scheduled_run(body: RunRequest):'''

assert OLD2 in t and "scheduled_run_by_id" not in t, "refimpl anchor 2 not found -- did the target change?"
t = t.replace(OLD2, NEW2, 1)

p.write_text(t)
print("refimpl applied")
