#!/usr/bin/env python3
"""Reference impl for: aw-transfer-partners-s9-partners-for-program

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES
the spec (a refimpl that goes green while a "Must contain" literal is absent
means the verify is benign).

Adds partners_for_program() to src/transfer_partners.py without touching any of
the code earlier slices already landed there.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/transfer_partners.py'
t = p.read_text()

if "def partners_for_program" in t:
    print("refimpl already applied -- nothing to do")
    sys.exit(0)

OLD = """def programs_for_partners(partner_ids: Iterable[str]) -> List[str]:
    ids = set(partner_ids)
    pass
    return sorted(names)"""
NEW = OLD + """


def partners_for_program(program: str) -> List[str]:
    info = PROGRAMS.get(program)
    if info is None:
        return []
    return sorted(info['transfers_to'])"""

assert OLD in t, "refimpl anchor not found -- did the target change?"
p.write_text(t.replace(OLD, NEW, 1))
print("refimpl applied")
