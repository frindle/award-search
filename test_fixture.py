"""Adversarial fixture for: aw-alert-filters-s4-filter-results

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
# '__dict__', so the fixture fails for a reason that has nothing to do with
# the task and the dispatch reads as a model failure.
sys.modules["target"] = target
spec.loader.exec_module(target)

RESULTS = [
    {"id": 1, "airlines": ["UA"], "severity": "high"},
    {"id": 2, "airlines": " dl ", "severity": "low"},
    {"id": 3, "severity": "high"},          # no airlines key at all
]


def _ids(results):
    return [r["id"] for r in results]


CASES = [
    # None filters: every result passes, original order preserved.
    ("None filters returns all results in order",
     lambda: _ids(target.filter_results(RESULTS, None)), [1, 2, 3]),

    # Empty-dict filters: same as no filters (falsy), not an error.
    ("empty dict filters returns all results",
     lambda: _ids(target.filter_results(RESULTS, {})), [1, 2, 3]),

    # Normalized matching via passes_filters: case-insensitive, stripped;
    # result 3 has no "airlines" key and must FAIL (never raise).
    ("filters keep only results whose airlines match, missing key fails",
     lambda: _ids(target.filter_results(RESULTS, {"airlines": ["DL"]})), [2]),

    # AND semantics across keys: both filters must hold on the same result.
    ("multiple filter keys are ANDed together",
     lambda: _ids(target.filter_results(RESULTS,
                                        {"airlines": "UA", "severity": "high"})), [1]),

    # No match at all -> empty list (not None, not an exception).
    ("no matching result yields an empty list",
     lambda: target.filter_results(RESULTS, {"airlines": ["XX"]}), []),

    # Empty input iterable -> empty list.
    ("empty results iterable yields an empty list",
     lambda: target.filter_results([], {"airlines": ["UA"]}), []),

    # Accepts any Iterable (a generator), consumed once.
    ("accepts a generator as the results iterable",
     lambda: _ids(target.filter_results((r for r in RESULTS), None)), [1, 2, 3]),

    # Returns a fresh list object; input dicts are shared, not copied.
    ("returns a new list sharing the same dict objects",
     lambda: (lambda out: out is not RESULTS and all(o in RESULTS for o in out))(
         target.filter_results(RESULTS, None)), True),
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
