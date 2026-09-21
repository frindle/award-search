#!/usr/bin/env python3
"""Reference impl for: aw-scheduled-searches-s3-cabins-business-first-pr

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES the
spec (a refimpl that goes green while a "Must contain" literal is absent means
the verify is benign).

Adds the `cabins`/`programs` defaults to DEFAULT_QUERY in
src/scheduled_searches.py, preserving everything already landed there.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/scheduled_searches.py'
t = p.read_text()

OLD = '''    "cabin": "business",
}'''
NEW = '''    "cabin": "business",
    'cabins':['business','first'],
    'programs':['united','flying_blue'],
}'''

assert OLD in t, "refimpl anchor not found -- did the target change?"
p.write_text(t.replace(OLD, NEW, 1))
print("refimpl applied")
