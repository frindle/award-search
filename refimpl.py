#!/usr/bin/env python3
"""Reference impl for: aw-sched-runner-s5-from-seats-aero-import-s

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

OLD = "from .scheduled_searches import effective_programs, is_due, load_schedules, query_legs, upsert_schedule"
NEW = (OLD + "\nfrom .seats_aero import SeatsAeroClient")

assert OLD in t, "refimpl anchor not found -- did the target change?"
assert "SeatsAeroClient" not in t, "import already present -- nothing to do"
p.write_text(t.replace(OLD, NEW, 1))
print("refimpl applied")
