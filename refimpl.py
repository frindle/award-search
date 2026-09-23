#!/usr/bin/env python3
"""Reference impl for: aw-sched-runner-s21-always-sets-sched-last-c

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

OLD = r'''def run_schedule(sched: Dict, client=None, notify: bool = True) -> List[Dict]:
    results = search_schedule(sched, client=client)
    if notify:
        for r in results:
            try:
                notify_hit(sched, r)
            except Exception:
                pass
    return results'''

NEW = r'''def run_schedule(sched: Dict, client=None, notify: bool = True) -> List[Dict]:
    sched['last_checked'] = datetime.now().isoformat()
    results = search_schedule(sched, client=client)
    if notify:
        for r in results:
            try:
                notify_hit(sched, r)
            except Exception:
                pass
    sched['last_results'] = results
    sched['last_hit_count'] = len(results)
    return results'''

assert OLD in t, "refimpl anchor not found -- did the target change?"
t = t.replace(OLD, NEW, 1)

if "from datetime import datetime" not in t:
    t = t.replace("from typing import Dict, List\n",
                  "from datetime import datetime\nfrom typing import Dict, List\n", 1)

p.write_text(t)
print("refimpl applied")
