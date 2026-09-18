#!/usr/bin/env python3
"""Reference impl for: aw-sched-runner-s1-from-alert-filters-impor

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
p.parent.mkdir(parents=True, exist_ok=True)

SOLUTION = '''\
"""Scheduled runner for saved alerts.

Re-checks each alert through search_fn on a cycle and keeps only the results
that pass the alert's filters (src/alert_filters.py). A malformed result or a
failing search must never abort the rest of the cycle.
"""
from .alert_filters import passes_filters


def select_results(alert, results):
    """Keep the results that pass this alert's filters, in original order.

    Filters come from alert["filters"]; a missing key or None means no
    restrictions (passes_filters is called with {}). A result for which
    passes_filters raises is dropped; the exception never propagates to the
    caller.
    """
    filters = alert.get("filters") or {}
    kept = []
    for r in results:
        try:
            ok = passes_filters(r, filters)
        except Exception:
            ok = False
        if ok:
            kept.append(r)
    return kept


def run_cycle(alerts, search_fn):
    """Run one check cycle over every alert.

    alerts maps id -> alert dict (None is treated as empty); search_fn(alert)
    returns the raw list of result dicts for that alert. Returns {id:
    kept_results} containing ONLY alerts with at least one kept result; an
    alert whose search raises is omitted and does not stop the cycle.
    """
    out = {}
    for aid, alert in (alerts or {}).items():
        try:
            results = search_fn(alert)
        except Exception:
            continue
        kept = select_results(alert, results)
        if kept:
            out[aid] = kept
    return out
'''

p.write_text(SOLUTION)
print("refimpl applied")
