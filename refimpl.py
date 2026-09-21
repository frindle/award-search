#!/usr/bin/env python3
"""Reference impl for: aw-transfer-partners-s8-programs-for-partners

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES
the spec (a refimpl that goes green while a "Must contain" literal is absent
means the verify is benign).

The target already contains PROGRAMS + list_partners() from earlier slices;
this ADDS programs_for_partners() without touching anything existing.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/transfer_partners.py'
t = p.read_text()

if "def programs_for_partners(" in t:
    print("refimpl already applied -- nothing to do")
    sys.exit(0)

OLD = """from typing import Dict, List"""
NEW = """from collections.abc import Iterable
from typing import Dict, List"""

assert OLD in t, "refimpl anchor not found -- did the target change?"
t = t.replace(OLD, NEW, 1)

ADDENDUM = '''

def programs_for_partners(partner_ids: Iterable[str]) -> List[str]:
    wanted = set(partner_ids)
    return sorted({info["name"] for info in PROGRAMS.values() if wanted & set(info["transfers_to"])})
'''
p.write_text(t.rstrip("\n") + "\n" + ADDENDUM)
print("refimpl applied")
