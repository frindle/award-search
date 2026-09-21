#!/usr/bin/env python3
"""Reference impl for: aw-transfer-partners-s7-list-partners

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
p = wt / 'src/transfer_partners.py'
t = p.read_text()

if "def list_partners" in t:
    print("refimpl already applied; nothing to do")
    sys.exit(0)

NEW = '''from typing import Dict, List


def list_partners() -> List[Dict]:
    """One dict per PROGRAMS entry -- {'id': slug, 'name', 'programs'} -- sorted by name."""
    partners = [
        {"id": slug, "name": info["name"], "programs": info["transfers_to"]}
        for slug, info in PROGRAMS.items()
    ]
    return sorted(partners, key=lambda partner: partner["name"])
'''

p.write_text(t.rstrip("\n") + "\n\n" + NEW)
print("refimpl applied")
