#!/usr/bin/env python3
"""Reference impl for: aw-sched-runner-s26-sleeps-poll-minutes-or-d

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
p = wt / 'src/scheduled_runner.py'
t = p.read_text()

OLD_IMPORTS = "from datetime import datetime\n"
NEW_IMPORTS = "import asyncio\nfrom datetime import datetime\n"
assert OLD_IMPORTS in t, "refimpl anchor (imports) not found -- did the target change?"
t = t.replace(OLD_IMPORTS, NEW_IMPORTS, 1)

OLD = r'''async def schedule_scheduler(poll_minutes: Optional[float] = None) -> None:
    pass'''
NEW = r'''DEFAULT_POLL_MINUTES = 5


async def schedule_scheduler(poll_minutes: Optional[float] = None) -> None:
    while True:
        await asyncio.sleep((poll_minutes or DEFAULT_POLL_MINUTES) * 60)'''

assert OLD in t, "refimpl anchor not found -- did the target change?"
p.write_text(t.replace(OLD, NEW, 1))
print("refimpl applied")
