#!/usr/bin/env python3
"""Reference impl for: aw-transfer-partners-s3-citi-typ-citi-thankyou-p

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES
the spec (a refimpl that goes green while a "Must contain" literal is absent
means the verify is benign).

This is a creation task -- the target is a stub docstring. The simplest
correct move is to overwrite it with the complete solution.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / "src/transfer_partners.py"
p.parent.mkdir(parents=True, exist_ok=True)

SOLUTION = '''\
"""Transfer partner lookup: which programs transfer into Citi ThankYou Points."""

TRANSFER_POINTS = {
    "flying_blue": "Citi ThankYou Points",
    "jetblue": "Citi ThankYou Points",
    "qantas": "Citi ThankYou Points",
    "qatar": "Citi ThankYou Points",
    "singapore": "Citi ThankYou Points",
    "turkish": "Citi ThankYou Points",
    "virgin_atlantic": "Citi ThankYou Points",
    "etihad": "Citi ThankYou Points",
    "emirates": "Citi ThankYou Points",
}


def get_transfer_points(program):
    """Return the transfer points for a program, or None if it does not transfer."""
    return TRANSFER_POINTS.get(program)
'''

p.write_text(SOLUTION)
print("refimpl applied")
