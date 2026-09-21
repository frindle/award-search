#!/usr/bin/env python3
"""Reference impl for: aw-sched-runner-s15-first-evaluate-passes-fi

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

OLD = """def select_results(alert, results):
    filters = alert.get("filters") or {}
    kept = []
    for r in results:
        try:
            if passes_filters(r, filters):
                kept.append(r)
        except Exception:
            continue
    return kept"""

NEW = """def select_results(alert, results):
    filters = alert.get("filters") or {}
    kept = []
    for r in results:
        try:
            first = dict(r)
            first["taxes"] = 0.0
            if not passes_filters(first, {k: v for k, v in filters.items() if k != "max_taxes"}):
                continue
            kept.append(r)
        except Exception:
            continue
    return kept"""

assert OLD in t, "refimpl anchor not found -- did the target change?"
p.write_text(t.replace(OLD, NEW, 1))
print("refimpl applied")
