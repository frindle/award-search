"""Adversarial fixture for: aw-alert-filters-s5-describe-filters

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


# Model-drafted; NOT yet read by a human.
DRAFT_UNCONFIRMED = True

CASES = [
    # --- describe_filters: the new behaviour ---------------------------------
    ("None filters -> no-filters summary",
     lambda: target.describe_filters(None), "(no filters)"),
    ("empty dict -> no-filters summary (falsy boundary)",
     lambda: target.describe_filters({}), "(no filters)"),
    ("lowercase codes are normalized uppercase, comma-joined",
     lambda: target.describe_filters({"airlines": ["ua", "NH"]}),
     "airlines UA,NH"),
    ("single code string is accepted like a one-item list",
     lambda: target.describe_filters({"airlines": "ua"}), "airlines UA"),
    ("whitespace around codes is stripped before joining",
     lambda: target.describe_filters({"airlines": [" ua ", "nh"]}),
     "airlines UA,NH"),
    ("empty code list renders the bare key, not a dangling space",
     lambda: target.describe_filters({"airlines": []}), "airlines"),
    ("multiple keys joined with '; ' in insertion order",
     lambda: target.describe_filters(
         {"airlines": ["UA"], "carriers": ["NH"]}),
     "airlines UA; carriers NH"),

    # --- regression half: earlier slices' work must keep working -------------
    ("normalize_airlines still normalizes (regression)",
     lambda: target.normalize_airlines([" ua ", 7, None, "nh"]),
     ["UA", "NH"]),
    ("passes_filters still passes on empty filters (regression)",
     lambda: target.passes_filters({"airlines": ["UA"]}, {}), True),
    ("filter_results still filters by normalized codes (regression)",
     lambda: target.filter_results(
         [{"airlines": ["ua"]}, {"airlines": ["NH"]}],
         {"airlines": "UA"}),
     [{"airlines": ["ua"]}]),
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
