#!/usr/bin/env python3
"""Reference impl for: aw-sched-runner-s7-seatsaeroclient-get-trip

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES
the spec (a refimpl that goes green while a "Must contain" literal is absent
means the verify is benign).

Adds get_trip(availability_id) to src/scheduled_runner.py on top of the code
already landed there by earlier slices; nothing existing is touched.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/scheduled_runner.py'
t = p.read_text()

NEW = '''

def get_trip(availability_id):
    client = SeatsAeroClient()
    try:
        trip = client.get_trip(availability_id)
    except Exception:
        return None
    if trip is None:
        return None
    trip.total_taxes = float(trip.total_taxes) / 100.0
    return trip
'''

if "def get_trip(" in t:
    print("refimpl already applied -- nothing to do")
else:
    p.write_text(t.rstrip() + "\n" + NEW)
    print("refimpl applied")
