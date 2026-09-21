"""Adversarial fixture for: aw-alert-filters-s1-filter-dict-airlines-ua

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

spec = importlib.util.spec_from_file_location("target", 'src/alert_filters.py')
target = importlib.util.module_from_spec(spec)
# REGISTER BEFORE EXEC. Not optional: a module loaded this way has no entry in
# sys.modules, so sys.modules[cls.__module__] is None -- and on Python 3.14 (the
# Studio worker) dataclasses resolves string annotations through exactly that
# lookup. A target with `from __future__ import annotations` + @dataclass then
# dies at IMPORT with AttributeError: 'NoneType' object has no attribute
# '__dict__', so the fixture fails for a reason that has nothing to do with the
# task and the dispatch reads as a model failure.
sys.modules["target"] = target
spec.loader.exec_module(target)


EXPECTED = {'airlines': ['UA', 'NH'], 'max_points': 90000, 'max_taxes': 100.0}


CASES = [
    # exact dict equality -- catches wrong values, extra/missing keys, and
    # airlines in the wrong order (['NH','UA'] != ['UA','NH'])
    ("get_filter() returns exactly the spec filter dict",
     lambda: target.get_filter(), EXPECTED),

    # airlines key: both codes present, UA first -- a plausible-but-wrong fix
    # that drops 'NH' or reorders fails here even if the other keys are right
    ("airlines is ['UA', 'NH'] in order",
     lambda: target.get_filter()['airlines'], ['UA', 'NH']),

    # max_points boundary value -- an off-by-one (9000/900000) fails here
    ("max_points is exactly 90000",
     lambda: target.get_filter()['max_points'], 90000),

    # max_taxes must be the float 100.0, not a string or int -- got != want
    # distinguishes '100.0' (str) from 100.0 (float)
    ("max_taxes is exactly 100.0",
     lambda: target.get_filter()['max_taxes'], 100.0),

    # repeated calls must be stable -- a mutable shared-state or randomised
    # implementation fails here
    ("second call returns the same dict",
     lambda: (target.get_filter(), target.get_filter())[1], EXPECTED),
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
