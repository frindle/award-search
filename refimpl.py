#!/usr/bin/env python3
"""Reference impl for: aw-transfer-partners-s10-restore-amex-mr-chase-ur

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES
the spec (a refimpl that goes green while a "Must contain" literal is absent
means the verify is benign).

The fix ADDS the amex_mr and chase_ur keys back into the EXISTING PROGRAMS
dict; it does not replace the dict wholesale. Everything else in the module
(citi_typ, capital_one, bilt, wells_fargo, and the three helper functions)
is preserved byte-for-byte.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/transfer_partners.py'
t = p.read_text()

OLD = r'''    "wells_fargo": {"name": "Wells Fargo Rewards",
                    "transfers_to": ["air_canada", "flying_blue", "virgin_atlantic"]},
}'''

NEW = r'''    "wells_fargo": {"name": "Wells Fargo Rewards",
                    "transfers_to": ["air_canada", "flying_blue", "virgin_atlantic"]},
    "amex_mr": {"name": "American Express Membership Rewards",
                "transfers_to": ["hyatt_worldwide", "marriott_bonvoy", "hilton_honors",
                                 "delta_sky_miles"]},
    "chase_ur": {"name": "Chase Ultimate Rewards",
                 "transfers_to": ["air_canada", "american", "united", "southwest",
                                  "jetblue", "british_airways", "singapore",
                                  "virgin_atlantic"]},
}'''

assert OLD in t, "refimpl anchor not found -- did the target change?"
p.write_text(t.replace(OLD, NEW, 1))
print("refimpl applied")
