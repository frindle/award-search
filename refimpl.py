#!/usr/bin/env python3
"""Reference impl for: aw-sched-runner-s10-search-schedule

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

OLD = """from typing import Dict
"""
NEW = """from typing import Dict, List
"""
assert OLD in t, "refimpl anchor not found -- did the target change?"
t = t.replace(OLD, NEW, 1)

if "def search_schedule(" in t:
    print("refimpl already applied")
    sys.exit(0)

ADD = """

def search_schedule(sched: Dict, client=None, today=None) -> List[Dict]:
    s = sched or {}
    return list(client.search(
        s.get("origin"),
        s.get("destination"),
        s.get("start_date") or today,
        s.get("end_date"),
        s.get("cabins"),
        s.get("programs"),
    ))
"""
p.write_text(t.rstrip() + "\n" + ADD)
print("refimpl applied")
