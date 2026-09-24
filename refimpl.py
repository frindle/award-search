#!/usr/bin/env python3
"""Reference impl for: aw-sched-runner-s27-use-module-level-logging

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFABLE as specified, and the verify actually ENFORCES the
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

# 1) stdlib import, alongside the existing top-of-file imports.
OLD_IMPORT = r'''import asyncio
from datetime import datetime'''
NEW_IMPORT = r'''import asyncio
import logging
from datetime import datetime'''

# 2) module-level logger, right after the existing constants block.
OLD_CONSTS = r'''NOTIFIED_KEYS_CAP = 200

DEFAULT_POLL_MINUTES = 5'''
NEW_CONSTS = r'''NOTIFIED_KEYS_CAP = 200

DEFAULT_POLL_MINUTES = 5

log = logging.getLogger(__name__)'''

# 3) exercise the logger in select_results' swallow-and-continue path.
OLD_SELECT_EXCEPT = r'''                kept.append(result)
        except Exception:
            continue'''
NEW_SELECT_EXCEPT = r'''                kept.append(result)
        except Exception:
            log.exception("select_results: dropping result %r", r.get("availability_id"))
            continue'''

# 4) exercise the logger in run_cycle's swallow-and-continue path.
OLD_CYCLE_EXCEPT = r'''    for alert_id, alert in (alerts or {}).items():
        try:
            results = search_fn(alert or {})
        except Exception:
            continue'''
NEW_CYCLE_EXCEPT = r'''    for alert_id, alert in (alerts or {}).items():
        try:
            results = search_fn(alert or {})
        except Exception:
            log.exception("run_cycle: search failed for alert %s", alert_id)
            continue'''

for old, new in [(OLD_IMPORT, NEW_IMPORT),
                 (OLD_CONSTS, NEW_CONSTS),
                 (OLD_SELECT_EXCEPT, NEW_SELECT_EXCEPT),
                 (OLD_CYCLE_EXCEPT, NEW_CYCLE_EXCEPT)]:
    assert old in t, "refimpl anchor not found -- did the target change? {!r}".format(old[:60])
    t = t.replace(old, new, 1)

p.write_text(t)
print("refimpl applied")
