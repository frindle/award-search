#!/usr/bin/env python3
"""Reference impl for: aw-transfer-partners-s6-wells-fargo-wells-fargo

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

if '"wells_fargo"' in t:
    print("refimpl already applied -- nothing to do")
    sys.exit(0)

# Anchor on the closing brace of the PROGRAMS dict; insert the new entry just
# before it, preserving every existing entry verbatim.
OLD = """}"""
NEW = '''    "wells_fargo": {"name": "Wells Fargo Rewards",
                    "transfers_to": ["air_canada", "flying_blue", "virgin_atlantic"]},
}'''

assert OLD in t, "refimpl anchor not found -- did the target change?"
# Replace only the LAST closing brace (the one ending PROGRAMS).
idx = t.rfind(OLD)
p.write_text(t[:idx] + NEW + t[idx + len(OLD):])
print("refimpl applied")
