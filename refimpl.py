#!/usr/bin/env python3
"""Reference impl for: aw-transfer-partners-s2-use-air-canada-american

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES the
spec (a refimpl that goes green while a "Must contain" literal is absent means
the verify is benign).

Adds the PROGRAMS['chase_ur'] entry to src/transfer_partners.py WITHOUT touching
the existing amex_mr entry -- this file is shared with sibling slices, so the
insertion must be additive.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/transfer_partners.py'
t = p.read_text()

if "'chase_ur'" in t:
    print("refimpl already applied -- nothing to do")
    sys.exit(0)

NEW = """    'chase_ur': {
        'name': 'Chase Ultimate Rewards',
        'transfers_to': [
            'air_canada',
            'american',
            'united',
            'southwest',
            'jetblue',
            'british_airways',
            'singapore',
            'virgin_atlantic',
        ],
    },

"""

# Insert the new entry just before the dict's final closing brace, keeping the
# existing amex_mr entry (and everything else in the file) byte-for-byte intact.
idx = t.rstrip().rfind('}')
assert idx != -1 and "PROGRAMS" in t, "refimpl anchor not found -- did the target change?"
t = t[:idx] + NEW + t[idx:]
p.write_text(t)
print("refimpl applied")
