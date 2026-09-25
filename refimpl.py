#!/usr/bin/env python3
"""Reference impl for: aw-sched-routes-s8-parse-cap

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES
the spec (a refimpl that goes green while a "Must contain" literal is absent
means the verify is benign).

Adds parse_cap to src/webui/scheduled_routes.py; everything already in the
file (routes, parse_csv, parse_date_ranges) is preserved untouched.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/webui/scheduled_routes.py'
t = p.read_text()

if "def parse_cap(" in t:
    print("refimpl already applied; nothing to do")
    sys.exit(0)

NEW = r'''

def parse_cap(value: Optional[str]) -> Optional[float|int]:
    """Parse a cap value from form input.

    None or blank strings mean "no cap" (None). A whole-number string is
    returned as an int; any other valid number as a float. Invalid values
    raise ValueError.
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        raise ValueError("invalid cap value") from None
    if number.is_integer():
        return int(number)
    return number
'''

p.write_text(t.rstrip("\n") + "\n" + NEW)
print("refimpl applied")
