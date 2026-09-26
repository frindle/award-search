"""Adversarial fixture for: aw-transfer-partners-s10-restore-amex-mr-chase-ur

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


CASES = [
    # --- the restored entries: exact values from s1/s2 ----------------------
    ("amex_mr is back in PROGRAMS with its exact name",
     lambda: target.PROGRAMS.get("amex_mr", {}).get("name"),
     "American Express Membership Rewards"),

    ("amex_mr transfers_to is exactly the four s1 partners (no aer_lingus)",
     lambda: sorted(target.PROGRAMS["amex_mr"]["transfers_to"]),
     ["delta_sky_miles", "hilton_honors", "hyatt_worldwide", "marriott_bonvoy"]),

    ("aer_lingus is NOT an amex_mr partner (plausible wrong fix)",
     lambda: "aer_lingus" in target.PROGRAMS["amex_mr"]["transfers_to"],
     False),

    ("chase_ur is back in PROGRAMS with its exact name",
     lambda: target.PROGRAMS.get("chase_ur", {}).get("name"),
     "Chase Ultimate Rewards"),

    ("chase_ur transfers_to is exactly the eight s2 partners",
     lambda: sorted(target.PROGRAMS["chase_ur"]["transfers_to"]),
     ["air_canada", "american", "british_airways", "jetblue", "singapore",
      "southwest", "united", "virgin_atlantic"]),

    # --- regression half: s3's entries and the pre-s1 ones must survive -----
    ("PROGRAMS still has all six programs (dict not replaced wholesale)",
     lambda: sorted(target.PROGRAMS.keys()),
     ["amex_mr", "bilt", "capital_one", "chase_ur", "citi_typ", "wells_fargo"]),

    ("citi_typ entry is byte-identical to what s3 left behind",
     lambda: target.PROGRAMS["citi_typ"],
     {"name": "Citi ThankYou Points",
      "transfers_to": ["flying_blue", "jetblue", "qantas", "qatar", "singapore",
                       "turkish", "virgin_atlantic", "etihad", "emirates"]}),

    ("wells_fargo entry is untouched",
     lambda: target.PROGRAMS["wells_fargo"],
     {"name": "Wells Fargo Rewards",
      "transfers_to": ["air_canada", "flying_blue", "virgin_atlantic"]}),

    # --- the helpers must see the restored entries --------------------------
    ("partners_for_program('amex_mr') returns its four partners sorted",
     lambda: target.partners_for_program("amex_mr"),
     ["delta_sky_miles", "hilton_honors", "hyatt_worldwide", "marriott_bonvoy"]),

    ("partners_for_program on an unknown program still returns [] (no raise)",
     lambda: target.partners_for_program("nope_unknown"),
     []),

    ("programs_for_partners(['hyatt_worldwide']) names amex_mr only",
     lambda: target.programs_for_partners(["hyatt_worldwide"]),
     ["American Express Membership Rewards"]),

    ("programs_for_partners(['virgin_atlantic']) includes chase_ur (restored)",
     lambda: target.programs_for_partners(["virgin_atlantic"]),
     # note: sorted() is case-sensitive, so capital-B "Bilt" lands last
     ["Bilt Rewards", "Capital One Miles", "Chase Ultimate Rewards",
      "Citi ThankYou Points", "Wells Fargo Rewards"]),

    ("programs_for_partners(['marriott_bonvoy']) names amex_mr only (restored)",
     lambda: target.programs_for_partners(["marriott_bonvoy"]),
     ["American Express Membership Rewards"]),

    ("list_partners() now lists 6 programs, sorted by name",
     lambda: [p["name"] for p in target.list_partners()],
     ["American Express Membership Rewards", "Bilt Rewards",
      "Capital One Miles", "Chase Ultimate Rewards", "Citi ThankYou Points",
      "Wells Fargo Rewards"]),

    ("list_partners() entry for amex_mr carries its program list",
     lambda: next(p["programs"] for p in target.list_partners() if p["id"] == "amex_mr"),
     ["hyatt_worldwide", "marriott_bonvoy", "hilton_honors", "delta_sky_miles"]),
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
