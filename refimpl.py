#!/usr/bin/env python3
"""Reference impl for: aw-sched-runner-s17-surviving-hits-get-resul

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

OLD = """def run_cycle(alerts, search_fn):
    out = {}
    for alert_id, alert in (alerts or {}).items():
        try:
            results = search_fn(alert or {})
        except Exception:
            continue
        kept = select_results(alert or {}, results)
        if kept:
            out[alert_id] = kept
    return out"""

NEW = """def _enrich_booking_urls(results):
    for result in (results or []):
        if not isinstance(result, dict):
            continue
        origin = result.get("origin")
        destination = result.get("destination")
        date = result.get("date")
        cabin = result.get("cabin")
        result['booking_url'] = seats_aero_url(origin, destination, date, cabin)


def run_cycle(alerts, search_fn):
    out = {}
    for alert_id, alert in (alerts or {}).items():
        try:
            results = search_fn(alert or {})
        except Exception:
            continue
        kept = select_results(alert or {}, results)
        if kept:
            _enrich_booking_urls(kept)
            out[alert_id] = [dict(r) for r in kept]
    return out"""

assert OLD in t, "refimpl anchor not found -- did the target change?"
p.write_text(t.replace(OLD, NEW, 1))
print("refimpl applied")
