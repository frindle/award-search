"""Adversarial fixture for: aw-scheduled-searches-s2-date-ranges-start-2026-0

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

spec = importlib.util.spec_from_file_location("target", 'src/scheduled_searches.py')
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

DEFAULTS = {"origin": "JFK", "destination": "LAX", "cabin": "business"}
DEF_RANGES = [{"start": "2026-03-01", "end": "2026-03-15"}]


def _q(ranges, **overrides):
    q = dict(DEFAULTS)
    q["date_ranges"] = ranges
    q.update(overrides)
    return q


CASES = [
    ("empty search returns the full default query",
     lambda: target.build_query({}),
     _q(DEF_RANGES)),

    ("None search must not raise and returns defaults",
     lambda: target.build_query(None),
     _q(DEF_RANGES)),

    ("single date becomes a one-day range, no raw 'date' key leaks out",
     lambda: target.build_query({"date": "2026-04-10"}),
     _q([{"start": "2026-04-10", "end": "2026-04-10"}])),

    ("out-of-order start/end are swapped, not returned as given",
     lambda: target.build_query({"start": "2026-05-20", "end": "2026-05-01"}),
     _q([{"start": "2026-05-01", "end": "2026-05-20"}])),

    ("explicit valid date_ranges pass through untouched, in order",
     lambda: target.build_query({"date_ranges": [
         {"start": "2026-03-01", "end": "2026-03-15"},
         {"start": "2026-06-01", "end": "2026-06-07"}]}),
     _q([{"start": "2026-03-01", "end": "2026-03-15"},
         {"start": "2026-06-01", "end": "2026-06-07"}])),

    ("invalid entries (None, str, missing key) are dropped, valid kept",
     lambda: target.build_query({"date_ranges": [
         None, "junk", {"start": "2026-02-01"},
         {"start": "2026-02-01", "end": "2026-02-14"}]}),
     _q([{"start": "2026-02-01", "end": "2026-02-14"}])),

    ("all-invalid date_ranges fall back to the defaults, no raise",
     lambda: target.build_query({"date_ranges": [None, 42]}),
     _q(DEF_RANGES)),

    ("empty-string dates are invalid and fall back to defaults",
     lambda: target.build_query({"date_ranges": [
         {"start": "", "end": "2026-01-01"},
         {"start": "2026-03-01", "end": ""}]}),
     _q(DEF_RANGES)),

    ("origin/cabin overrides merge over defaults, ranges stay default",
     lambda: target.build_query({"origin": "SFO", "cabin": "first"}),
     _q(DEF_RANGES, origin="SFO", cabin="first")),
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
