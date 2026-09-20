#!/usr/bin/env python3
"""Reference impl for: aw-sched-runner-s3-from-pushover-import-sen

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
p = wt / 'src' / 'scheduled_runner.py'
p.parent.mkdir(parents=True, exist_ok=True)

SOLUTION = '''from .alert_filters import passes_filters
from .pushover import send_award_notification


def select_results(alert, results):
    filters = alert.get("filters") or {}
    kept = []
    for r in results:
        try:
            if passes_filters(r, filters):
                kept.append(r)
        except Exception:
            continue
    return kept


def notify_result(result):
    """Send the Pushover award notification for one kept result.

    Never raises: a missing credential or a transport error degrades to
    False so one bad alert cannot kill the whole cycle.
    """
    try:
        return bool(send_award_notification(
            origin=result.get("origin", ""),
            destination=result.get("destination", ""),
            date=result.get("date", ""),
            program=result.get("program", ""),
            miles=int(result.get("miles") or 0),
            cabin=result.get("cabin", ""),
            seats=int(result.get("seats") or 0),
            booking_url=result.get("booking_url"),
        ))
    except Exception:
        return False


def run_cycle(alerts, search_fn):
    out = {}
    for alert_id, alert in (alerts or {}).items():
        try:
            results = search_fn(alert or {})
        except Exception:
            continue
        kept = select_results(alert or {}, results)
        if not kept:
            continue
        out[alert_id] = kept
        for result in kept:
            notify_result(result)
    return out
'''

p.write_text(SOLUTION)
print("refimpl applied")
