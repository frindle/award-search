"""Adversarial fixture for: aw-transfer-partners-s6-wells-fargo-wells-fargo

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

spec = importlib.util.spec_from_file_location("target", 'src/transfer_partners.py')
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
    ("wells_fargo entry exists with exact name",
     lambda: target.PROGRAMS["wells_fargo"]["name"], "Wells Fargo Rewards"),
    ("wells_fargo transfers_to is exactly the three partners, in order",
     lambda: target.PROGRAMS["wells_fargo"]["transfers_to"],
     ["air_canada", "flying_blue", "virgin_atlantic"]),
    ("entry shape has exactly the two required keys",
     lambda: sorted(target.PROGRAMS["wells_fargo"].keys()),
     ["name", "transfers_to"]),
    ("regression: citi_typ entry unchanged",
     lambda: target.PROGRAMS["citi_typ"],
     {"name": "Citi ThankYou Points",
      "transfers_to": ["flying_blue", "jetblue", "qantas", "qatar", "singapore",
                       "turkish", "virgin_atlantic", "etihad", "emirates"]}),
    ("regression: capital_one entry unchanged",
     lambda: target.PROGRAMS["capital_one"],
     {"name": "Capital One Miles",
      "transfers_to": ["air_canada", "emirates", "etihad", "finnair", "flying_blue",
                       "qantas", "singapore", "turkish", "virgin_atlantic", "qatar"]}),
    ("regression: bilt entry unchanged",
     lambda: target.PROGRAMS["bilt"],
     {"name": "Bilt Rewards",
      "transfers_to": ["air_canada", "american", "emirates", "flying_blue", "turkish",
                       "united", "virgin_atlantic", "alaska"]}),
    ("PROGRAMS has exactly the four known slugs (no extras, none missing)",
     lambda: sorted(target.PROGRAMS.keys()),
     ["bilt", "capital_one", "citi_typ", "wells_fargo"]),
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
