#!/usr/bin/env python3
"""Reference impl for: aw-transfer-partners-s5-bilt-bilt-rewards-air-ca

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

if '"bilt"' in t:
    print("refimpl already applied -- nothing to do")
    sys.exit(0)

OLD = '''    "capital_one": {"name": "Capital One Miles",
                    "transfers_to": ["air_canada", "emirates", "etihad", "finnair", "flying_blue",
                                     "qantas", "singapore", "turkish", "virgin_atlantic", "qatar"]},
}'''

NEW = '''    "capital_one": {"name": "Capital One Miles",
                    "transfers_to": ["air_canada", "emirates", "etihad", "finnair", "flying_blue",
                                     "qantas", "singapore", "turkish", "virgin_atlantic", "qatar"]},
    "bilt": {"name": "Bilt Rewards",
             "transfers_to": ["air_canada", "american", "emirates", "flying_blue", "turkish",
                              "united", "virgin_atlantic", "alaska"]},
}'''

assert OLD in t, "refimpl anchor not found -- did the target change?"
p.write_text(t.replace(OLD, NEW, 1))
print("refimpl applied")
