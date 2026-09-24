#!/usr/bin/env python3
"""Reference impl for: aw-sched-runner-s25-sleeps-20s-then-forever

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES
the spec (a refimpl that goes green while a "Must contain" literal is absent
means the verify is benign).

Write the SIMPLEST change that makes the verify pass. It doubles as your review
reference when the model's diff comes back.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/scheduled_runner.py'
t = p.read_text()

OLD = r'''async def schedule_scheduler(poll_minutes: Optional[float] = None) -> None:
    while True:
        await asyncio.sleep((poll_minutes or DEFAULT_POLL_MINUTES) * 60)
'''

NEW = r'''async def schedule_scheduler(poll_minutes: Optional[float] = None) -> None:
    # sleeps 20s, then forever: load_schedules(), run every schedule where is_due(s) via asyncio.to_thread(run_schedule, s).
    await asyncio.sleep(20)
    while True:
        for s in (load_schedules() or []):
            try:
                if is_due(s):
                    await asyncio.to_thread(run_schedule, s)
            except Exception:
                log.exception("schedule_scheduler: failed to process schedule %r", (s or {}).get("id"))
        await asyncio.sleep((poll_minutes or DEFAULT_POLL_MINUTES) * 60)
'''

assert OLD in t, "refimpl anchor not found -- did the target change?"
p.write_text(t.replace(OLD, NEW, 1))
print("refimpl applied")
