"""Adversarial fixture for: aw-transfer-partners-s3-citi-typ-citi-thankyou-p

>>> THE ONE THING THE GENERATOR CANNOT WRITE FOR YOU <<<

CASES is empty and the verify FAILS until you fill it in. That is deliberate.
A generator can emit a verify that DISCRIMINATES (fails at baseline, passes on
a fix). It cannot decide whether the verify is RELEVANT -- whether it tests the
property the task actually asked for. A benign case passes broken work.

Pick inputs that separate "did the job" from "made the test go green":
  * the exact boundary the defect is about, and one on each side of it
  * the degenerate inputs (missing key, None, wrong type) that must NOT
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

TP = "Citi ThankYou Points"
EXPECTED_PROGRAMS = {
    "flying_blue", "jetblue", "qantas", "qatar", "singapore",
    "turkish", "virgin_atlantic", "etihad", "emirates",
}


def _all_programs_resolve():
    """Every one of the nine partners must resolve to Citi ThankYou Points --
    a mapping missing even one partner (or spelling it wrong) fails here."""
    return {p: target.get_transfer_points(p) for p in EXPECTED_PROGRAMS} == \
        dict.fromkeys(EXPECTED_PROGRAMS, TP)


CASES = [
    ("all nine partners map to Citi ThankYou Points", _all_programs_resolve, True),

    ("TRANSFER_POINTS has exactly the nine partner keys (no extras)",
     lambda: set(target.TRANSFER_POINTS.keys()) == EXPECTED_PROGRAMS, True),

    ("every TRANSFER_POINTS value is 'Citi ThankYou Points'",
     lambda: all(v == TP for v in target.TRANSFER_POINTS.values()), True),

    ("unknown program returns None (not a KeyError)",
     lambda: target.get_transfer_points("aeroplan"), None),

    ("lookup is case-sensitive: 'Flying Blue' does not resolve",
     lambda: target.get_transfer_points("Flying Blue"), None),

    ("None input must not raise and resolves to nothing",
     lambda: target.get_transfer_points(None), None),

    ("empty-string program resolves to nothing",
     lambda: target.get_transfer_points(""), None),
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
