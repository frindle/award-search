#!/usr/bin/env python3
"""Reference impl for: aw-transfer-partners-s4-capital-one-capital-one

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES the
spec (a refimpl that goes green while a "Must contain" literal is absent means
the verify is benign).

Adds the capital_one entry to PROGRAMS in src/transfer_partners.py, preserving
everything already there (e.g. the citi_typ entry from s3). Idempotent: if the
entry is already present it leaves the file untouched.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/transfer_partners.py'
t = p.read_text()

if '"capital_one"' in t:
    print("refimpl already applied -- nothing to do")
    sys.exit(0)

NEW = '''    "capital_one": {"name": "Capital One Miles",
                    "transfers_to": ["air_canada", "emirates", "etihad", "finnair",
                                     "flying_blue", "qantas", "singapore", "turkish",
                                     "virgin_atlantic", "qatar"]},
'''

# Insert the new entry just before the closing brace of PROGRAMS, keeping the
# existing entries (citi_typ) intact.
idx = t.rfind('}')
assert idx != -1 and 'PROGRAMS' in t, "refimpl anchor not found -- did the target change?"
t = t[:idx] + NEW + t[idx:]
p.write_text(t)
print("refimpl applied")
