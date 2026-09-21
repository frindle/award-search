#!/usr/bin/env python3
"""Reference impl for: aw-scheduled-searches-s1-id-sched-ab12-name-bay-a

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES the
spec (a refimpl that goes green while a "Must contain" literal is absent means
the verify is benign).

The target is a one-line stub (creation task), so this writes the complete
solution file.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/scheduled_searches.py'
p.parent.mkdir(parents=True, exist_ok=True)

SOLUTION = '''"""Scheduled searches registry for the award search tool."""

SCHEDULED_SEARCHES = [
    {
        'id': 'sched_ab12',
        'name': 'Bay Area to Tokyo',
        'enabled': True,
        'origin': ['SFO', 'OAK', 'SJC'],
        'destination': ['HND', 'NRT'],
        'cabin': 'business',
    },
]


def get_scheduled_search(search_id):
    """Return the scheduled search whose id equals `search_id`, else None."""
    for entry in SCHEDULED_SEARCHES:
        if entry['id'] == search_id:
            return entry
'''

p.write_text(SOLUTION)
print("refimpl applied")
