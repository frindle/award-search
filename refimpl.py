#!/usr/bin/env python3
"""Reference impl for: aw-sched-runner-s22-then-union-the-new-keys

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

# Add NOTIFIED_KEYS_CAP constant after imports (before first def).
OLD_CONST_ANCHOR = "def select_results(alert, results):"
NEW_CONST_BLOCK = r'''NOTIFIED_KEYS_CAP = 200


def select_results(alert, results):'''

assert OLD_CONST_ANCHOR in t, "refimpl anchor for const not found -- did the target change?"
t = t.replace(OLD_CONST_ANCHOR, NEW_CONST_BLOCK, 1)

# Modify run_schedule to union new keys into sched['notified_keys'].
OLD_RUN = r'''def run_schedule(sched: Dict, client=None, notify: bool = True) -> List[Dict]:
    results = search_schedule(sched, client=client)
    if notify:
        for r in results:
            try:
                notify_hit(sched, r)
            except Exception:
                pass
    sched['last_checked'] = datetime.now().isoformat()'''

NEW_RUN = r'''def run_schedule(sched: Dict, client=None, notify: bool = True) -> List[Dict]:
    results = search_schedule(sched, client=client)
    if notify:
        for r in results:
            try:
                notify_hit(sched, r)
            except Exception:
                pass
    # then union the new keys into sched['notified_keys'] (sorted, trimmed to the LAST NOTIFIED_KEYS_CAP).
    already = set(sched.get("notified_keys") or [])
    already.update(_result_key(r) for r in results)
    sched["notified_keys"] = sorted(already)[-NOTIFIED_KEYS_CAP:]
    sched['last_checked'] = datetime.now().isoformat()'''

assert OLD_RUN in t, "refimpl anchor for run_schedule not found -- did the target change?"
t = t.replace(OLD_RUN, NEW_RUN, 1)

p.write_text(t)
print("refimpl applied")
