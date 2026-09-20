"""Adversarial fixture for: aw-airport-groups-s2-expand-codes

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


CASES = [
    # Uppercasing: lowercase input must come back uppercase.
    ("lowercase codes are uppercased", lambda: target.expand_codes(["jfk", "lga"]), ["JFK", "LGA"]),

    # Order-preserving dedupe: first-seen order, NOT sorted (a sorted() impl fails this).
    ("order is preserved, not sorted", lambda: target.expand_codes(["b", "a", "c"]), ["B", "A", "C"]),

    # Case-insensitive dedupe: jfk/JFK/Jfk are one code (exact-match set/dict fails this).
    ("duplicates differing only in case collapse to one", lambda: target.expand_codes(["jfk", "JFK", "Jfk"]), ["JFK"]),

    # Duplicates keep the FIRST position, not the last.
    ("duplicate keeps its first-seen position", lambda: target.expand_codes(["x", "y", "X"]), ["X", "Y"]),

    # Empty input is a valid boundary: no raise, empty list back.
    ("empty input returns an empty list", lambda: target.expand_codes([]), []),

    # Iterable (not just list): a generator must work -- catches len()/index() impls.
    ("accepts any iterable, e.g. a generator", lambda: target.expand_codes(c for c in ["a", "b", "A"]), ["A", "B"]),

    # Single element passes through uppercased.
    ("single code is uppercased and returned alone", lambda: target.expand_codes(["ord"]), ["ORD"]),

    # Already-uppercase input is unchanged (regression half).
    ("already-uppercase codes pass through untouched", lambda: target.expand_codes(["SFO", "SEA"]), ["SFO", "SEA"]),
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
