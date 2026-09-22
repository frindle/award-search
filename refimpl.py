#!/usr/bin/env python3
"""Reference impl for: aw-app-wiring-s6-sched-task-asyncio-creat

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES the
spec (a refimpl that goes green while a "Must contain" literal is absent means
the verify is benign).

Adds to src/webui/app.py (preserving everything already there):
  1. an async stub `schedule_scheduler()` coroutine at module level, and
  2. `sched_task = asyncio.create_task(schedule_scheduler())` inside lifespan(),
     directly after the existing alert-scheduler task line.
"""
import pathlib

wt = pathlib.Path(__file__).resolve().parent
p = wt / 'src/webui/app.py'
t = p.read_text()

ANCHOR_DEF = "@asynccontextmanager\n"
STUB = (
    "async def schedule_scheduler():\n"
    '    """Placeholder for the scheduled-routes scheduler loop (later slice)."""\n'
    "    return None\n"
    "\n"
    "\n"
)

ANCHOR_TASK = (
    "    task = asyncio.create_task(alert_scheduler(_alert_search, _alert_notify, interval))\n"
)
TASK_LINE = ANCHOR_TASK + "    sched_task = asyncio.create_task(schedule_scheduler())\n"

assert ANCHOR_DEF in t, "refimpl anchor (@asynccontextmanager) not found -- did the target change?"
assert ANCHOR_TASK in t, "refimpl anchor (alert task line) not found -- did the target change?"
t = t.replace(ANCHOR_DEF, STUB + ANCHOR_DEF, 1)
t = t.replace(ANCHOR_TASK, TASK_LINE, 1)
p.write_text(t)
print("refimpl applied")
