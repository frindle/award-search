#!/usr/bin/env python3
"""Reference impl for: aw-sched-runner-s9-result-key

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES
the spec (a refimpl that goes green while a "Must contain" literal is absent
means the verify is benign).

Adds _result_key(r) to src/scheduled_runner.py on top of the code already
landed there by earlier slices; nothing existing is touched.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/scheduled_runner.py'
t = p.read_text()

NEW = '''

def _result_key(r: Dict) -> str:
    return "|".join([
        str((r or {}).get("program", "")),
        str((r or {}).get("origin", "")),
        str((r or {}).get("destination", "")),
        str((r or {}).get("date", "")),
        str((r or {}).get("cabin", "")),
    ])
'''

if "def _result_key(" in t:
    print("refimpl already applied -- nothing to do")
else:
    if "from typing import Dict" not in t and "Dict" not in t.split("\n")[0]:
        # ensure the annotation's name resolves at def time
        t = t.replace(
            "from .alert_filters import passes_filters",
            "from typing import Dict\nfrom .alert_filters import passes_filters",
            1,
        )
    p.write_text(t.rstrip() + "\n" + NEW)
    print("refimpl applied")
