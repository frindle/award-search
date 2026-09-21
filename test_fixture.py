"""Adversarial fixture for: aw-alert-filters-s3-passes-filters

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


CASES = [
    # No filters at all -> always passes (None must not raise).
    ("filters=None passes anything",
     lambda: target.passes_filters({"airlines": ["UA"]}, None), True),

    # Empty dict filter is the same as no filters.
    ("empty dict filter passes",
     lambda: target.passes_filters({}, {}), True),

    # Case-insensitive, whitespace-stripped match via normalize_airlines.
    ("case/whitespace-insensitive codes match",
     lambda: target.passes_filters({"airlines": [" ua ", "DL"]},
                                   {"airlines": ["UA", "dl"]}), True),

    # Subset is NOT a pass: result missing one requested code -> False.
     ("subset of requested codes fails",
     lambda: target.passes_filters({"airlines": ["UA"]},
                                   {"airlines": ["UA", "DL"]}), False),

    # Extra code in the result is also a mismatch (order-sensitive equality).
    ("extra code in result fails",
     lambda: target.passes_filters({"airlines": ["UA", "AA"]},
                                   {"airlines": ["UA"]}), False),

    # Filter key absent from result -> False, and it must NOT raise.
    ("missing filter key fails without raising",
     lambda: target.passes_filters({}, {"airlines": ["UA"]}), False),

    # Multiple keys: every one must hold; one bad key sinks the whole thing.
    ("all keys must match, one mismatch fails",
     lambda: target.passes_filters({"airlines": ["UA"], "cabin": "business"},
                                   {"airlines": ["UA"], "cabin": "first"}), False),

    # Multiple keys all satisfied -> True.
    ("multiple matching keys pass",
     lambda: target.passes_filters({"airlines": ["UA"], "cabin": "BUSINESS"},
                                   {"airlines": ["ua"], "cabin": "business"}), True),
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
