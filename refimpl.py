#!/usr/bin/env python3
"""Reference impl for: aw-sched-runner-s18-notify-hit

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

OLD = r'''def search_schedule(sched: Dict, client=None, today=None) -> List[Dict]:
    c = client or SeatsAeroClient()
    s = sched or {}
    return list(c.search(
        s.get("origin"),
        s.get("destination"),
        s.get("start_date"),
        s.get("end_date"),
        s.get("cabins"),
        s.get("programs"),
    ))'''

NEW = r'''def search_schedule(sched: Dict, client=None, today=None) -> List[Dict]:
    c = client or SeatsAeroClient()
    s = sched or {}
    return list(c.search(
        s.get("origin"),
        s.get("destination"),
        s.get("start_date"),
        s.get("end_date"),
        s.get("cabins"),
        s.get("programs"),
    ))


def notify_hit(sched: Dict, r: Dict) -> None:
    s = sched or {}
    res = r or {}
    send_award_notification(
        s.get("origin"),
        s.get("destination"),
        s.get("date"),
        program=res.get("source"),
        miles=res.get("cost"),
        cabin=res.get("cabin"),
        seats=res.get("seats"),
        booking_url=res.get("booking_url"),
    )'''

assert OLD in t, "refimpl anchor not found -- did the target change?"
p.write_text(t.replace(OLD, NEW, 1))
print("refimpl applied")
