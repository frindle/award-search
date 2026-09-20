"""Adversarial fixture for: aw-airport-groups-s3-group-label

>>> THE ONE THING THE GENERATOR CANNOT WRITE FOR YOU <<<

CASES is empty and the verify FAILS until you fill it in. That is deliberate.
A generator can emit a verify that DISCRIMINATES (fails at baseline, passes on
a fix). It cannot decide whether the verify is RELEVANT -- whether it tests the
property the task actually asked for. A benign case passes broken work.

Pick inputs that separate "did the job" from "made the test go green":
  * the exact boundary the defect is about, and one on each side of it
  * the degenerate inputs (missing key, None, empty, wrong type) that must NOT
    raise
  * at least one case that a plausible WRONG fix would fail
  * the regression half: things that already work and must keep working

Each case: (description, callable_returning_actual, expected)
"""
import sys
import importlib.util

spec = importlib.util.spec_from_file_location("target", 'src/airport_groups.py')
target = importlib.util.module_from_spec(spec)
# REGISTER BEFORE EXEC. Not optional: a module loaded this way has no entry in
# sys.modules, so sys.modules[cls.__module__] is None -- and on Python 3.14 (the
# Studio worker) dataclasses resolves string annotations through exactly that
# lookup. A target with `from __future__ import annotations` + @dataclass then
# dies at IMPORT with AttributeError: 'NoneType' object has no attribute
# '__dict__', so the fixture fails for a reason that has nothing to do with
# the task and the dispatch reads as a model failure.
sys.modules["target"] = target
spec.loader.exec_module(target)

# Data-agnostic adversarial cases: whatever groups the solution defines, EVERY
# one of them must resolve through group_label to its own 'name', and any code
# NOT in AIRPORT_GROUPS must fall through to itself (a plausible wrong fix --
# raising KeyError on unknown codes, or returning the name for every input --
# fails these).

GROUPS = target.AIRPORT_GROUPS  # dict: code -> {"name": ...}


def _unknown_code():
    """A code guaranteed absent from AIRPORT_GROUPS."""
    for cand in ("ZZZ", "QQQ", "XXX", "UNKNOWN-CODE"):
        if cand not in GROUPS:
            return cand
    raise AssertionError("no unknown code available")


CASES = [
    # The lookup table exists and is non-empty (a bare `AIRPORT_GROUPS = {}`
    # would otherwise pass everything below vacuously).
    ("AIRPORT_GROUPS defines at least one group", lambda: len(GROUPS) >= 1, True),
]

# One case per defined group -- every data line in the table is exercised.
for _code, _entry in GROUPS.items():
    CASES.append((
        "known code {!r} resolves to its group name".format(_code),
        lambda c=_code: target.group_label(c),
        _entry["name"],
    ))

# The spec's canonical groups are pinned by name AND label: a table that
# renames "JFK" -> "JFK_X" (or relabels it) would still pass the data-driven
# loop above, because both sides of the lookup move together. These cases pin
# the exact code->label pairs from TASK.md so such drift is caught.
CASES -= [
    ("canonical group 'JFK' resolves to exactly 'New York (JFK)'",
     lambda: target.group_label("JFK"), "New York (JFK)"),
    ("canonical group 'LHR' resolves to exactly 'London (LHR)'",
     lambda: target.group_label("LHR"), "London (LHR)"),
]

CASES += [
    # Unknown code falls through to the code itself and must NOT raise.
    ("unknown code is returned unchanged",
     lambda: (lambda u: target.group_label(u) == u)(_unknown_code()), True),
    # Degenerate input must not raise; with no group it maps to itself.
    ("empty string does not raise and returns itself",
     lambda: target.group_label(""), GROUPS[""]["name"] if "" in GROUPS else ""),
    # Regression half: the pre-existing helper keeps working untouched.
    ("expand_codes still dedupes case-insensitively",
     lambda: target.expand_codes(["jfk", "JFK", "lhr"]), ["JFK", "LHR"]),
]


def main():
    if len(CASES) < 3:
        print("  SCAFFOLD_INCOMPLETE: {} adversarial case(s) authored, need >= 3."
              .format(len(CASES)))
        print("  A generated scaffold is not a verify. Author the cases in "
              "test_fixture.py.")
        return 1
    fails = 0
    for desc, thunk, want in CASES:
        try:
            got = thunk()
        except Exception as e:
            print("  FAIL {} -- raised {}: {}".format(desc, type(e).__name__, e))
            fails += 1
            continue
        if got != want:
            print("  FAIL {} -- got {!r}, want {!r}".format(desc, got, want))
            fails += 1
    print("  {}/{} case(s) passed".format(len(CASES) - fails, len(CASES)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
