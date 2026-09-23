#!/usr/bin/env python3
"""Reference impl for: aw-sched-runner-s24-schedule-scheduler

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES
the spec (a refimpl that goes green while a "Must contain" literal is absent
means the verify is benign).

Adds `async def schedule_scheduler(poll_minutes: Optional[float] = None) -> None`
to src/scheduled_runner.py (plus `Optional` on the typing import), preserving
every function already landed by earlier slices. The tick loop body itself is
slices s25/s26 -- this slice only establishes the awaitable coroutine.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/scheduled_runner.py'
t = p.read_text()

OLD_IMPORT = "from typing import Dict, List"
NEW_IMPORT = "from typing import Dict, List, Optional"
assert OLD_IMPORT in t, "typing import anchor not found -- did the target change?"
assert "schedule_scheduler" not in t, "schedule_scheduler already present?"
t = t.replace(OLD_IMPORT, NEW_IMPORT, 1)

ADD = '''

async def schedule_scheduler(poll_minutes: Optional[float] = None) -> None:
    """Background scheduler entry point; the tick loop lands in slices s25/s26."""
    return None
'''
p.write_text(t.rstrip("\n") + "\n" + ADD)
print("refimpl applied")
