#!/usr/bin/env python3
"""Reference impl for: aw-transfer-partners-s1-amex-mr-american-express

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES
the spec (a refimpl that goes green while a "Must contain" literal is absent
means the verify is benign).

Write the SIMPLEST change that makes the verify pass. It doubles as your review
reference when the model's diff comes back.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/transfer_partners.py'
p.parent.mkdir(parents=True, exist_ok=True)

SOLUTION = '''\
"""Transfer partner programs for loyalty points platforms.

PROGRAMS is keyed by program slug; each entry carries the display name and
the list of slugs it can transfer to. aer_lingus is NOT a valid amex_mr
transfer partner and must stay out of its transfers_to list.
"""

PROGRAMS = {
    'amex_mr': {
        'name': 'American Express Membership Rewards',
        'transfers_to': [
            'hyatt',
            'marriott',
            'hilton',
            'delta_sky_miles',
            'british_airways_executive_club',
            'flying_blue',
        ],
    },
}
'''

p.write_text(SOLUTION)
print("refimpl applied")
