"""Adversarial fixture for: aw-transfer-partners-s8-programs-for-partners

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
# '__dict__', so the fixture fails for a reason that has nothing to do with
# the task and the dispatch reads as a model failure.
sys.modules["target"] = target
spec.loader.exec_module(target)

ALL_FOUR = ["Bilt Rewards", "Capital One Miles", "Citi ThankYou Points",
            "Wells Fargo Rewards"]

CASES = [
    # one partner that only two programs transfer to -- exact names, sorted
    ("etihad -> exactly the two programs that list it, sorted",
     lambda: target.programs_for_partners(["etihad"]),
     ["Capital One Miles", "Citi ThankYou Points"]),

    # UNION across ids (OR semantics): etihad hits citi+capital, united hits bilt.
    # An AND/intersection implementation returns [] here and fails this case.
    ("union across partner_ids is OR, not intersection",
     lambda: target.programs_for_partners(["etihad", "united"]),
     ["Bilt Rewards", "Capital One Miles", "Citi ThankYou Points"]),

    # de-duplication: flying_blue AND qantas both hit citi_typ and capital_one.
    # A per-(program, id) append implementation returns each name twice here.
    ("names are de-duplicated when several ids match the same program",
     lambda: target.programs_for_partners(["flying_blue", "qantas"]),
     ALL_FOUR),

    # a partner no program transfers to -> empty list, not an error
    ("unknown partner id yields []",
     lambda: target.programs_for_partners(["no_such_partner"]),
     []),

    # degenerate input: empty iterable must not raise and yields []
    ("empty partner_ids yields [] without raising",
     lambda: target.programs_for_partners([]),
     []),

    # regression half: list_partners() from the earlier slice still works
    ("list_partners() still returns all 4 partners sorted by name",
     lambda: [p["name"] for p in target.list_partners()],
     ALL_FOUR),

    # regression half: list_partners() entries keep their shape
    ("list_partners() entries keep id/name/programs keys and data",
     lambda: {p["id"]: (p["name"], sorted(p["programs"]))
              for p in target.list_partners()}["wells_fargo"],
     ("Wells Fargo Rewards", ["air_canada", "flying_blue", "virgin_atlantic"])),
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
