#!/usr/bin/env python3
"""Reference impl for: aw-sched-runner-s2-from-deeplinks-import-se

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES
the spec (a refimpl that goes green while a "Must contain" literal is absent
means the verify is benign).

Writes the complete solution into src/scheduled_runner.py: keeps the existing
select_results/run_cycle behaviour intact and adds booking_links(), which
attaches a seats.aero deep link to each result via .deeplinks.seats_aero_url.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/scheduled_runner.py'
p.parent.mkdir(parents=True, exist_ok=True)

SOLUTION = '''from .alert_filters import passes_filters
from .deeplinks import seats_aero_url


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


def run_cycle(alerts, search_fn):
    out = {}
    for alert_id, alert in (alerts or {}).items():
        try:
            results = search_fn(alert or {})
        except Exception:
            continue
        kept = select_results(alert or {}, results)
        if kept:
            out[alert_id] = kept
    return out


def booking_links(alert, results):
    """Return new result dicts, each augmented with a seats.aero booking_url.

    The alert supplies origin/destination/cabin; missing keys fall back to ""
    and "economy". Input results are never mutated -- callers get fresh dicts.
    """
    alert = alert or {}
    out = []
    for r in (results or []):
        linked = dict(r) if isinstance(r, dict) else {"result": r}
        linked["booking_url"] = seats_aero_url(
            alert.get("origin", ""),
            alert.get("destination", ""),
            alert.get("date", ""),
            alert.get("cabin", "economy"),
        )
        out.append(linked)
    return out
'''

p.write_text(SOLUTION)
print("refimpl applied")
