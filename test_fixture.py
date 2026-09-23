"""Adversarial fixture for: aw-alert-filters-contract

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


R_HIT = {"airlines": ["NH", "JL"], "cost": 85000, "taxes": 95.5}

CASES = [
    # --- no filters / unknown keys -----------------------------------------
    ("None filters pass anything", lambda: target.passes_filters(R_HIT, None), True),
    ("empty filter dict passes anything", lambda: target.passes_filters(R_HIT, {}), True),
    ("unknown/extra filter keys are ignored, not a False",
     lambda: target.passes_filters(R_HIT, {"cabin": "business"}), True),

    # --- airlines: intersection semantics ----------------------------------
    ("allowlist intersects result carriers -> pass (not list equality)",
     lambda: target.passes_filters({"airlines": ["NH", "JL"]}, {"airlines": ["UA", "NH"]}), True),
    ("single-code allowlist string matches one of several carriers",
     lambda: target.passes_filters(R_HIT, {"airlines": "ua"}), False),
    ("allowlist disjoint from result carriers -> fail",
     lambda: target.passes_filters({"airlines": ["NH"]}, {"airlines": ["UA", "DL"]}), False),
    ("missing result airlines with allowlist set fails closed",
     lambda: target.passes_filters({"cost": 100}, {"airlines": ["UA"]}), False),
    ("None result airlines with allowlist set fails closed (no raise)",
     lambda: target.passes_filters({"airlines": None, "cost": 100}, {"airlines": ["UA"]}), False),
    ("empty allowlist imposes nothing",
     lambda: target.passes_filters({"airlines": []}, {"airlines": []}), True),
    ("non-normalizable allowlist (int) fails closed, never raises",
     lambda: target.passes_filters(R_HIT, {"airlines": 123}), False),

    # --- max_points: inclusive cap on cost ---------------------------------
    ("cost exactly at the points cap PASSES (inclusive boundary)",
     lambda: target.passes_filters(R_HIT, {"max_points": 85000}), True),
    ("cost above the points cap fails",
     lambda: target.passes_filters(R_HIT, {"max_points": 84999}), False),
    ("missing cost with a points cap fails closed (no raise)",
     lambda: target.passes_filters({"airlines": ["UA"]}, {"max_points": 90000}), False),
    ("None cost with a points cap fails closed",
     lambda: target.passes_filters({"cost": None}, {"max_points": 90000}), False),

    # --- max_taxes: inclusive cap on taxes ---------------------------------
    ("taxes exactly at the taxes cap PASSES (inclusive boundary)",
     lambda: target.passes_filters(R_HIT, {"max_taxes": 95.5}), True),
    ("taxes above the taxes cap fails",
     lambda: target.passes_filters(R_HIT, {"max_taxes": 95.49}), False),
    ("None taxes with a taxes cap fails closed (two-pass drop)",
     lambda: target.passes_filters({"cost": 100}, {"max_taxes": 100.0}), False),

    # --- AND of applied constraints ----------------------------------------
    ("all three set and all pass -> True",
     lambda: target.passes_filters(R_HIT, {"airlines": ["NH"], "max_points": 90000, "max_taxes": 100.0}), True),
    ("one failing constraint among passing ones -> False",
     lambda: target.passes_filters(R_HIT, {"airlines": ["UA"], "max_points": 90000, "max_taxes": 100.0}), False),

    # --- describe_filters: numeric caps must not raise ---------------------
    ("describe_filters renders a numeric points cap without TypeError",
     lambda: target.describe_filters({"max_points": 90000}), "max_points 90000"),
    ("describe_filters renders all three constraints",
     lambda: target.describe_filters({"airlines": ["UA", "NH"], "max_points": 90000, "max_taxes": 100.0}),
     "airlines UA,NH; max_points 90000; max_taxes 100.0"),
    ("describe_filters(None) is '(no filters)'",
     lambda: target.describe_filters(None), "(no filters)"),

    # --- regression half: normalize_airlines / filter_results unchanged ----
    ("normalize_airlines still normalizes a list of codes",
     lambda: target.normalize_airlines([" ua ", "nh"]), ["UA", "NH"]),
    ("filter_results keeps passing results in order and drops the rest",
     lambda: target.filter_results(
         [{"airlines": ["UA"], "cost": 50}, {"airlines": ["DL"], "cost": 999},
          {"airlines": ["UA"], "cost": 1}],
         {"max_points": 60}),
     [{"airlines": ["UA"], "cost": 50}, {"airlines": ["UA"], "cost": 1}]),
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
    print("  {}/{} case(s) passed".format(len(CASES) - fails, len(CASES)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
