#!/usr/bin/env python3
"""Reference impl for: aw-sched-runner-s19-run-schedule

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES the
spec (a refimpl that goes green while a "Must contain" literal is absent means
the verify is benign).

The target already contains search_schedule() and notify_hit() from earlier
slices; this slice only ADDS run_schedule() on top of them. Everything else in
src/scheduled_runner.py is preserved verbatim.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/scheduled_runner.py'
t = p.read_text()

assert "def run_schedule(" not in t, "run_schedule already present -- did the target change?"

NEW = r'''

def run_schedule(sched: Dict, client=None, notify: bool = True) -> List[Dict]:
    results = search_schedule(sched, client=client)
    if notify:
        for r in results:
            try:
                notify_hit(sched, r)
            except Exception:
                pass
    return results
'''

p.write_text(t.rstrip("\n") + "\n" + NEW)
print("refimpl applied")
